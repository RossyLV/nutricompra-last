"""Validación de los datos que entran al sistema.

Regla de oro: nunca confiar en lo que llega del usuario.
Cada función revisa un dato y, si está mal, lanza ErrorValidacion con un
mensaje en español que se puede mostrar tal cual en la pantalla.
"""
import math

from app import config


class ErrorValidacion(ValueError):
    """Se lanza cuando un dato de entrada no es válido."""


def validar_presupuesto(valor) -> float:
    """Valida el presupuesto semanal en soles. Debe ser un número mayor que 0."""
    # bool es un tipo de entero en Python (True == 1), por eso se rechaza aparte
    if isinstance(valor, bool):
        raise ErrorValidacion("El presupuesto debe ser un número.")
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        raise ErrorValidacion("El presupuesto debe ser un número.")
    if math.isnan(numero) or math.isinf(numero):
        raise ErrorValidacion("El presupuesto debe ser un número válido.")
    if numero <= 0:
        raise ErrorValidacion("El presupuesto debe ser mayor que 0.")
    if numero > config.PRESUPUESTO_MAXIMO:
        raise ErrorValidacion(
            f"El presupuesto no puede superar S/ {config.PRESUPUESTO_MAXIMO:,.0f}."
        )
    return numero


def validar_personas(valor) -> int:
    """Valida la cantidad de personas del hogar. Entero entre 1 y el máximo."""
    if isinstance(valor, bool):
        raise ErrorValidacion("La cantidad de personas debe ser un número entero.")
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        raise ErrorValidacion("La cantidad de personas debe ser un número entero.")
    # 2.5 personas no tiene sentido: se exige un entero exacto
    if math.isnan(numero) or math.isinf(numero) or numero != int(numero):
        raise ErrorValidacion("La cantidad de personas debe ser un número entero.")
    entero = int(numero)
    if entero < 1:
        raise ErrorValidacion("Debe haber al menos 1 persona.")
    if entero > config.PERSONAS_MAXIMO:
        raise ErrorValidacion(f"El máximo es {config.PERSONAS_MAXIMO} personas.")
    return entero


def validar_categoria(valor) -> str:
    """Valida que la categoría sea una de las categorías del catálogo."""
    if not isinstance(valor, str):
        raise ErrorValidacion("La categoría debe ser un texto.")
    categoria = valor.strip().lower()
    if categoria not in config.CATEGORIAS_CATALOGO:
        permitidas = ", ".join(config.CATEGORIAS_CATALOGO)
        raise ErrorValidacion(f"Categoría no válida. Opciones: {permitidas}.")
    return categoria


def validar_imagen(tipo_mime, tamano_bytes) -> None:
    """Valida el tipo y el tamaño de una foto subida.

    Solo se aceptan JPG y PNG, no vacías y de hasta TAMANO_MAX_IMAGEN_MB.
    """
    if tipo_mime not in config.FORMATOS_IMAGEN_PERMITIDOS:
        raise ErrorValidacion("Formato no permitido. Sube una imagen JPG o PNG.")
    if not isinstance(tamano_bytes, int) or tamano_bytes <= 0:
        raise ErrorValidacion("La imagen está vacía.")
    maximo_bytes = config.TAMANO_MAX_IMAGEN_MB * 1024 * 1024
    if tamano_bytes > maximo_bytes:
        raise ErrorValidacion(
            f"La imagen es muy grande. El máximo es {config.TAMANO_MAX_IMAGEN_MB} MB."
        )
