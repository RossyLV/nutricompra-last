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

    Así el catálogo se encuentra sin importar desde dónde se ejecute el programa.
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
# (aceites, semillas, azúcar).
CATEGORIA_OTRO: str = "otro"
CATEGORIAS_CATALOGO: tuple[str, ...] = CATEGORIAS_APP + (CATEGORIA_OTRO,)

# Comidas de un menú semanal: 7 días x 3 comidas.
DIAS_SEMANA: int = 7
COMIDAS_POR_DIA: int = 3
TOTAL_COMIDAS_SEMANA: int = DIAS_SEMANA * COMIDAS_POR_DIA  # 21

# Límites razonables para validar lo que escribe el usuario.
PRESUPUESTO_MAXIMO: float = 100_000.0  # soles por semana
PERSONAS_MAXIMO: int = 20

# Formatos de imagen aceptados al subir una foto.
FORMATOS_IMAGEN_PERMITIDOS: tuple[str, ...] = ("image/jpeg", "image/png")
