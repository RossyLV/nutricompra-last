"""Configuración central de los servicios de IA de NutriCompra.

Aquí se leen las variables de entorno (nada de secretos en el código)
y se definen las constantes que usa el resto del sistema.
"""
import os
from pathlib import Path

# Carpeta "servicios-ia" (dos niveles arriba de este archivo: app -> api -> servicios-ia)
DIRECTORIO_BASE: Path = Path(__file__).resolve().parents[2]


def _resolver_ruta(ruta: str) -> Path:
    """Convierte una ruta relativa en absoluta, partiendo de servicios-ia.

    Así los archivos de datos se encuentran sin importar desde dónde se ejecute el programa.
    """
    camino = Path(ruta)
    return camino if camino.is_absolute() else DIRECTORIO_BASE / camino


def _leer_entero_positivo(nombre: str, por_defecto: int) -> int:
    """Lee una variable de entorno como entero mayor que cero.

    Si no existe, está vacía o no es válida, devuelve el valor por defecto.
    """
    valor = os.getenv(nombre, "")
    try:
        numero = int(valor)
    except ValueError:
        return por_defecto
    return numero if numero > 0 else por_defecto


# --- Valores que vienen del entorno (.env) con un valor por defecto ---
ENTORNO: str = os.getenv("ENTORNO", "desarrollo")
MODELO_HF: str = os.getenv("MODELO_HF", "nateraw/food")
RUTA_CATALOGO: Path = _resolver_ruta(os.getenv("RUTA_CATALOGO", "datos/catalogo.csv"))
RUTA_EQUIVALENCIAS: Path = _resolver_ruta(
    os.getenv("RUTA_EQUIVALENCIAS", "datos/equivalencias.csv")
)
TAMANO_MAX_IMAGEN_MB: int = _leer_entero_positivo("TAMANO_MAX_IMAGEN_MB", 5)

# --- Constantes fijas del dominio ---
# Las 5 categorías que usa la aplicación para el balance nutricional.
CATEGORIAS_APP: tuple[str, ...] = (
    "vegetal",
    "carbohidrato",
    "proteina",
    "fruta",
    "lacteo",
)
# Alimentos que están en el catálogo pero no cuentan para el balance
# (aceites, semillas, azúcar, postres).
CATEGORIA_OTRO: str = "otro"
CATEGORIAS_CATALOGO: tuple[str, ...] = CATEGORIAS_APP + (CATEGORIA_OTRO,)

# Comidas de un menú semanal: 7 días x 3 comidas.
DIAS_SEMANA: int = 7
COMIDAS_POR_DIA: int = 3
TOTAL_COMIDAS_SEMANA: int = DIAS_SEMANA * COMIDAS_POR_DIA  # 21

# Límites razonables para validar lo que escribe el usuario.
PRESUPUESTO_MAXIMO: float = 100_000.0  # soles por semana
PERSONAS_MAXIMO: int = 20

# Formatos de imagen aceptados al subir una foto (tipo MIME y formato real).
FORMATOS_IMAGEN_PERMITIDOS: tuple[str, ...] = ("image/jpeg", "image/png")
FORMATOS_REALES_PERMITIDOS: tuple[str, ...] = ("JPEG", "PNG")

# Clasificador de imágenes
CANTIDAD_PREDICCIONES: int = 3      # se devuelven las 3 más probables (top-3)
UMBRAL_CONFIANZA: float = 0.40      # por debajo de esto se avisa "poca confianza"

# ---------------------------------------------------------------------------
# Recomendador de menús (Fase 3)
# ---------------------------------------------------------------------------
# Momentos del día y de qué categorías se arma cada comida.
# Cada comida es una combinación de INGREDIENTES del catálogo (no hay recetas).
MOMENTOS_DEL_DIA: tuple[str, ...] = ("desayuno", "almuerzo", "cena")
ESTRUCTURA_COMIDAS: dict[str, tuple[str, ...]] = {
    "desayuno": ("carbohidrato", "lacteo", "fruta"),
    "almuerzo": ("carbohidrato", "proteina", "vegetal"),
    "cena": ("carbohidrato", "proteina", "vegetal"),
}

# Porción por persona de cada categoría, en gramos (peso crudo). Simplificación:
# todas las personas del hogar comen la misma porción de adulto.
PORCIONES_G: dict[str, int] = {
    "carbohidrato": 120,
    "proteina": 120,
    "vegetal": 100,
    "fruta": 150,
    "lacteo": 200,
}

# Excepciones de porción (por persona, en gramos): alimentos que se comen en
# cantidades distintas a las de su categoría. Se busca primero por nombre y
# luego por la categoría original de la TPCA.
PORCIONES_ESPECIALES_POR_NOMBRE_G: dict[str, int] = {
    "Queso fresco": 40,
    "Queso fresco de cabra": 40,
    "Leche evaporada entera": 100,
    "Leche evaporada descremada": 100,
}
PORCIONES_ESPECIALES_POR_TPCA_G: dict[str, int] = {"Legumbres": 80}  # secas

# Ingredientes que están en el catálogo pero no se usan como base de una comida:
# condimentos (ajo, culantro) y la harina de trigo (no se come sola; el fideo ya cubre la pasta).
INGREDIENTES_EXCLUIDOS: tuple[str, ...] = ("Ajo", "Culantro", "Harina de trigo")

# Requerimientos nutricionales DIARIOS de referencia para un adulto, por persona.
# tipo "minimo": basta con llegar a "min" (pasarse no se penaliza).
# tipo "rango": lo ideal es estar entre "min" y "max".
# Son valores de referencia generales, NO una recomendación médica individual.
REQUERIMIENTOS: dict[str, dict] = {
    "energy_kcal": {"nombre": "Energía (kcal)", "tipo": "rango", "min": 1800, "max": 2400},
    "protein_g": {"nombre": "Proteína (g)", "tipo": "minimo", "min": 50},
    "fat_g": {"nombre": "Grasa (g)", "tipo": "rango", "min": 44, "max": 78},
    "calcium_mg": {"nombre": "Calcio (mg)", "tipo": "minimo", "min": 1000},
    "iron_mg": {"nombre": "Hierro (mg)", "tipo": "minimo", "min": 12},
}
NUTRIENTES_BALANCE: tuple[str, ...] = tuple(REQUERIMIENTOS)

# Reglas de variedad del menú
MAX_REPETICIONES_SEMANA: int = 4   # un mismo ingrediente, máximo 4 veces por semana

# Búsqueda del mejor menú (mejora por intercambios)
ITERACIONES_BUSQUEDA: int = 3000
SEMILLA_POR_DEFECTO: int = 42      # misma semilla = mismo menú (resultados repetibles)

# Pesos de la función objetivo (qué tanto importa cada cosa)
PESO_VARIEDAD: float = 0.05
PESO_PREFERENCIA: float = 0.15
PESO_COSTO: float = 0.02           # a igual nutrición, se prefiere el menú más barato
PREFERENCIA_NEUTRA: float = 0.5    # puntaje de un alimento sin "me gusta" ni "no me gusta"
