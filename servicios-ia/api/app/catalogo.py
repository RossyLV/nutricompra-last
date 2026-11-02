"""Lectura y consulta del catálogo de alimentos (archivo CSV).

El catálogo se puede reemplazar por datos reales cambiando el CSV,
siempre que mantenga los mismos nombres de columna.
"""
import csv
from pathlib import Path

from app import config

# Columnas con valores numéricos (nutrientes por 100 g y precio).
COLUMNAS_NUMERICAS: tuple[str, ...] = (
    "reference_amount",
    "energy_kcal",
    "protein_g",
    "carbohydrate_g",
    "fat_g",
    "fiber_g",
    "sodium_mg",
    "calcium_mg",
    "iron_mg",
    "price_per_kg_ref",
)

COLUMNAS_OBLIGATORIAS: tuple[str, ...] = (
    "name",
    "category",
    "app_category",
    "price_per_kg_ref",
) + COLUMNAS_NUMERICAS[:-1]


def _a_numero(texto: str):
    """Convierte un texto en número. Una celda vacía devuelve None.

    IMPORTANTE: vacío significa "la fuente no tiene este dato", NO es cero.
    Un 0 medido y un dato faltante son cosas distintas.
    """
    texto = texto.strip()
    if texto == "":
        return None
    return float(texto)


def cargar_catalogo(ruta: Path | None = None) -> list[dict]:
    """Lee el CSV y devuelve una lista de alimentos (diccionarios).

    Lanza ValueError si falta una columna o hay una categoría inválida.
    """
    ruta = ruta or config.RUTA_CATALOGO
    alimentos: list[dict] = []
    with open(ruta, encoding="utf-8", newline="") as archivo:
        lector = csv.DictReader(archivo)
        faltantes = [c for c in COLUMNAS_OBLIGATORIAS if c not in (lector.fieldnames or [])]
        if faltantes:
            raise ValueError(f"Al catálogo le faltan columnas: {', '.join(faltantes)}")
        for numero_fila, fila in enumerate(lector, start=2):
            for columna in COLUMNAS_NUMERICAS:
                try:
                    fila[columna] = _a_numero(fila[columna])
                except ValueError:
                    raise ValueError(
                        f"Fila {numero_fila}: valor no numérico en '{columna}'."
                    )
            if fila["app_category"] not in config.CATEGORIAS_CATALOGO:
                raise ValueError(
                    f"Fila {numero_fila}: categoría de la app no válida "
                    f"('{fila['app_category']}')."
                )
            alimentos.append(fila)
    return alimentos


def buscar_alimento(catalogo: list[dict], nombre: str) -> dict | None:
    """Busca un alimento por nombre, sin importar mayúsculas. None si no existe."""
    buscado = nombre.strip().lower()
    for alimento in catalogo:
        if alimento["name"].lower() == buscado:
            return alimento
    return None


def filtrar_por_categoria(catalogo: list[dict], categoria: str) -> list[dict]:
    """Devuelve solo los alimentos de una categoría de la app."""
    return [a for a in catalogo if a["app_category"] == categoria]


def obtener_precio(catalogo: list[dict], nombre: str) -> float | None:
    """Precio en soles por kg de un alimento. None si no existe.

    ÚNICO PUNTO DE ENTRADA PARA PRECIOS: hoy lee el precio de referencia del
    CSV. Cuando el backend tenga precios reales, solo se cambia esta función
    y el recomendador, las pruebas y el dashboard siguen igual.
    """
    alimento = buscar_alimento(catalogo, nombre)
    return alimento["price_per_kg_ref"] if alimento else None
