"""Clasificación de fotos de alimentos con un modelo PREENTRENADO.

Flujo: foto -> modelo de Hugging Face (nateraw/food, clases de Food-101)
-> tabla de equivalencias (CSV) -> categoría de la app + alimento del catálogo
(con su precio y valores nutricionales).

No se entrena nada: solo se reutiliza un modelo existente.
"""
import csv
import io
from functools import lru_cache
from pathlib import Path
from typing import Callable

from PIL import Image, UnidentifiedImageError

from app import config
from app.catalogo import buscar_alimento
from app.validacion import ErrorValidacion, validar_imagen

# Un "predictor" es cualquier función que recibe una imagen (PIL) y devuelve una
# lista ordenada de {"label": str, "score": float}. Así podemos probar el resto
# del código con un predictor falso, sin descargar el modelo.
Predictor = Callable[[Image.Image], list[dict]]

# Campos del catálogo que se devuelven junto con la predicción.
CAMPOS_ALIMENTO: tuple[str, ...] = (
    "name",
    "category",
    "app_category",
    "price_per_kg_ref",
    "energy_kcal",
    "protein_g",
    "carbohydrate_g",
    "fat_g",
    "fiber_g",
    "calcium_mg",
    "iron_mg",
)


def normalizar_etiqueta(etiqueta: str) -> str:
    """Deja la etiqueta del modelo en minúsculas y con guion bajo ("Apple Pie" -> "apple_pie")."""
    return etiqueta.strip().lower().replace(" ", "_").replace("-", "_")


def cargar_equivalencias(ruta: Path | None = None, catalogo: list[dict] | None = None) -> dict[str, dict]:
    """Lee la tabla de equivalencias y la valida contra el catálogo.

    Devuelve un diccionario {clase_food101: fila}. Lanza ValueError si:
    - la categoría no es válida,
    - el alimento indicado no existe en el catálogo,
    - la categoría de la fila no coincide con la del alimento del catálogo.
    """
    ruta = ruta or config.RUTA_EQUIVALENCIAS
    equivalencias: dict[str, dict] = {}
    with open(ruta, encoding="utf-8", newline="") as archivo:
        for numero_fila, fila in enumerate(csv.DictReader(archivo), start=2):
            clase = normalizar_etiqueta(fila["clase_food101"])
            if clase in equivalencias:
                raise ValueError(f"Fila {numero_fila}: clase repetida '{clase}'.")
            if fila["app_category"] not in config.CATEGORIAS_CATALOGO:
                raise ValueError(f"Fila {numero_fila}: categoría no válida '{fila['app_category']}'.")
            nombre_alimento = fila["alimento_catalogo"].strip()
            if catalogo is not None and nombre_alimento:
                alimento = buscar_alimento(catalogo, nombre_alimento)
                if alimento is None:
                    raise ValueError(f"Fila {numero_fila}: '{nombre_alimento}' no está en el catálogo.")
                if alimento["app_category"] != fila["app_category"]:
                    raise ValueError(
                        f"Fila {numero_fila}: la categoría no coincide con la de '{nombre_alimento}'."
                    )
            equivalencias[clase] = fila
    return equivalencias


def abrir_imagen(contenido: bytes) -> Image.Image:
    """Abre la imagen y comprueba que REALMENTE sea JPG o PNG (no solo el nombre)."""
    try:
        imagen = Image.open(io.BytesIO(contenido))
        formato = imagen.format
        imagen.load()  # fuerza a leer todo: detecta archivos corruptos
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise ErrorValidacion("No se pudo leer la imagen. Prueba con otra foto JPG o PNG.")
    if formato not in config.FORMATOS_REALES_PERMITIDOS:
        raise ErrorValidacion("Formato no permitido. Sube una imagen JPG o PNG.")
    return imagen.convert("RGB")  # el modelo espera 3 canales de color


@lru_cache
def obtener_predictor() -> Predictor:
    """Carga el modelo de Hugging Face (solo la primera vez; luego queda en memoria).

    La primera ejecución descarga el modelo (~350 MB). Corre en CPU.
    """
    # Se importa aquí adentro para que las pruebas no necesiten instalar torch.
    from transformers import pipeline

    clasificador = pipeline("image-classification", model=config.MODELO_HF, device=-1)

    def predecir(imagen: Image.Image) -> list[dict]:
        return clasificador(imagen, top_k=config.CANTIDAD_PREDICCIONES)

    return predecir


def _armar_prediccion(resultado: dict, catalogo: list[dict], equivalencias: dict[str, dict]) -> dict:
    """Convierte una predicción del modelo en una respuesta con categoría y alimento."""
    clase = normalizar_etiqueta(resultado["label"])
    fila = equivalencias.get(clase)
    prediccion = {
        "clase": clase,
        "nombre": fila["nombre_es"] if fila else clase.replace("_", " ").capitalize(),
        "probabilidad": round(float(resultado["score"]), 4),
        "categoria": fila["app_category"] if fila else None,
        "alimento": None,
    }
    if fila and fila["alimento_catalogo"].strip():
        alimento = buscar_alimento(catalogo, fila["alimento_catalogo"])
        if alimento:
            prediccion["alimento"] = {campo: alimento[campo] for campo in CAMPOS_ALIMENTO}
    return prediccion


def clasificar_imagen(
    contenido: bytes,
    tipo_mime: str,
    predictor: Predictor,
    catalogo: list[dict],
    equivalencias: dict[str, dict],
) -> dict:
    """Clasifica una foto y la enlaza con el catálogo.

    Pasos: validar -> abrir -> predecir top-3 -> mapear cada clase.
    Lanza ErrorValidacion si la imagen no es válida.
    """
    validar_imagen(tipo_mime, len(contenido))
    imagen = abrir_imagen(contenido)

    resultados = predictor(imagen)[: config.CANTIDAD_PREDICCIONES]
    predicciones = [_armar_prediccion(r, catalogo, equivalencias) for r in resultados]

    principal = predicciones[0]
    confiable = principal["probabilidad"] >= config.UMBRAL_CONFIANZA
    if not confiable:
        mensaje = "No estoy seguro de qué alimento es. Prueba con una foto más clara."
    elif principal["categoria"] is None:
        mensaje = "Reconocí el plato, pero no está en la tabla de equivalencias."
    else:
        mensaje = f"Parece {principal['nombre']} ({principal['categoria']})."
    return {"confiable": confiable, "mensaje": mensaje, "predicciones": predicciones}
