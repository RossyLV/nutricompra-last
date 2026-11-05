"""Validación de los datos que entran al sistema.

Regla de oro: nunca confiar en lo que llega del usuario.
Cada función revisa un dato y, si está mal, lanza ErrorValidacion con un
mensaje en español que se puede mostrar tal cual en la pantalla.
"""
import math
import re

from app import config

# Un identificador de usuario solo puede tener letras, números, punto, guion y guion bajo.
_PATRON_USUARIO_ID = re.compile(r"[A-Za-z0-9_.\-]+")


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


def validar_usuario_id(valor) -> str:
    """Valida el identificador del usuario (ej. "familia_perez").

    Texto de 1 a USUARIO_ID_MAX_LARGO caracteres, solo letras, números, ".", "-" y "_".
    """
    if not isinstance(valor, str):
        raise ErrorValidacion("El identificador de usuario debe ser un texto.")
    usuario = valor.strip()
    if not usuario:
        raise ErrorValidacion("El identificador de usuario no puede estar vacío.")
    if len(usuario) > config.USUARIO_ID_MAX_LARGO:
        raise ErrorValidacion(
            f"El identificador de usuario no puede superar {config.USUARIO_ID_MAX_LARGO} caracteres."
        )
    if not _PATRON_USUARIO_ID.fullmatch(usuario):
        raise ErrorValidacion(
            "El identificador de usuario solo puede tener letras, números, punto, guion y guion bajo."
        )
    return usuario


def validar_voto(valor) -> str:
    """Valida el voto: debe ser "me_gusta" o "no_me_gusta"."""
    if not isinstance(valor, str) or valor.strip().lower() not in config.VOTOS_VALIDOS:
        opciones = ", ".join(config.VOTOS_VALIDOS)
        raise ErrorValidacion(f"Voto no válido. Opciones: {opciones}.")
    return valor.strip().lower()


def validar_mensaje_chat(valor) -> str:
    """Valida la pregunta del chat: texto no vacío de hasta CHAT_MENSAJE_MAX_LARGO caracteres."""
    if not isinstance(valor, str):
        raise ErrorValidacion("El mensaje debe ser un texto.")
    mensaje = valor.strip()
    if not mensaje:
        raise ErrorValidacion("El mensaje no puede estar vacío.")
    if len(mensaje) > config.CHAT_MENSAJE_MAX_LARGO:
        raise ErrorValidacion(f"El mensaje no puede superar {config.CHAT_MENSAJE_MAX_LARGO} caracteres.")
    return mensaje


def validar_historial_chat(valor) -> list[dict]:
    """Valida la conversación previa: lista de {"role": "user"|"assistant", "content": texto}.

    Es opcional (None = conversación nueva). Se devuelve una copia limpia con solo esas dos claves.
    """
    if valor is None:
        return []
    if not isinstance(valor, list):
        raise ErrorValidacion("El historial debe ser una lista de mensajes.")
    if len(valor) > config.CHAT_HISTORIAL_MAX_MENSAJES:
        raise ErrorValidacion(
            f"El historial no puede tener más de {config.CHAT_HISTORIAL_MAX_MENSAJES} mensajes."
        )
    limpio: list[dict] = []
    for numero, item in enumerate(valor, start=1):
        if not isinstance(item, dict):
            raise ErrorValidacion(f"El mensaje {numero} del historial no es válido.")
        rol, contenido = item.get("role"), item.get("content")
        if rol not in config.ROLES_CHAT:
            opciones = ", ".join(config.ROLES_CHAT)
            raise ErrorValidacion(f"El mensaje {numero} del historial tiene un rol no válido. Opciones: {opciones}.")
        if not isinstance(contenido, str) or not contenido.strip():
            raise ErrorValidacion(f"El mensaje {numero} del historial debe tener texto.")
        if len(contenido) > config.CHAT_HISTORIAL_MAX_LARGO:
            raise ErrorValidacion(
                f"El mensaje {numero} del historial supera {config.CHAT_HISTORIAL_MAX_LARGO} caracteres."
            )
        limpio.append({"role": rol, "content": contenido})
    return limpio


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
