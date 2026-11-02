"""Configuración central de los servicios de IA de NutriCompra.

Aquí se leen las variables de entorno (nada de secretos en el código)
y se definen las constantes que usa el resto del sistema.
"""
import os

# --- Valores que vienen del entorno (.env) con un valor por defecto ---
ENTORNO: str = os.getenv("ENTORNO", "desarrollo")
MODELO_HF: str = os.getenv("MODELO_HF", "nateraw/food")
RUTA_CATALOGO: str = os.getenv("RUTA_CATALOGO", "datos/catalogo.csv")


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

# Comidas de un menú semanal: 7 días x 3 comidas.
DIAS_SEMANA: int = 7
COMIDAS_POR_DIA: int = 3
TOTAL_COMIDAS_SEMANA: int = DIAS_SEMANA * COMIDAS_POR_DIA  # 21

# Formatos de imagen aceptados al subir una foto.
FORMATOS_IMAGEN_PERMITIDOS: tuple[str, ...] = ("image/jpeg", "image/png")
