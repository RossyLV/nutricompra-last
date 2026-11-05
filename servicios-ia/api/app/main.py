"""API (FastAPI) de los servicios de IA de NutriCompra.

Expone el catálogo, la clasificación de fotos, la recomendación de menús y las
preferencias del usuario ("me gusta / no me gusta") para que el prototipo y el
dashboard los consuman.
"""
from functools import lru_cache
from typing import Any

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app import catalogo as cat
from app import chat, clasificador, config, preferencias, recomendador
from app.almacen import Almacen
from app.validacion import (
    ErrorValidacion,
    validar_categoria,
    validar_historial_chat,
    validar_mensaje_chat,
    validar_usuario_id,
    validar_voto,
)

app = FastAPI(
    title="NutriCompra Inteligente - Servicios de IA",
    description="Catálogo, clasificación de alimentos, recomendación de menús, preferencias y chat.",
    version="0.4.0",
)


class EntradaRecomendacion(BaseModel):
    """Datos para armar el menú. Se declaran como "Any" a propósito: la validación
    (y sus mensajes en español) la hace app.validacion, no pydantic."""

    presupuesto: Any = Field(..., description="Presupuesto semanal en soles (> 0)", examples=[200])
    personas: Any = Field(..., description="Personas del hogar (>= 1)", examples=[4])
    usuario_id: Any = Field(
        None,
        description="Opcional. Si se indica, el menú se adapta a los 'me gusta / no me gusta' de ese usuario.",
        examples=["familia_perez"],
    )


class EntradaVoto(BaseModel):
    """Un voto del usuario sobre un alimento (también validado en app.validacion)."""

    usuario_id: Any = Field(..., description="Identificador del usuario o familia", examples=["familia_perez"])
    alimento: Any = Field(..., description="Nombre del alimento tal como está en el catálogo", examples=["Quinua"])
    voto: Any = Field(..., description="'me_gusta' o 'no_me_gusta'", examples=["me_gusta"])


class EntradaChat(BaseModel):
    """Una pregunta al asistente, con la conversación previa (opcional).

    El servicio no guarda conversaciones: quien llama (la web o el dashboard) envía el historial.
    """

    mensaje: Any = Field(..., description="Pregunta del usuario (máx. 500 caracteres)", examples=["¿Qué alimento barato tiene hierro?"])
    historial: Any = Field(
        None,
        description="Opcional. Lista de {'role': 'user' | 'assistant', 'content': texto}, máx. 10 mensajes.",
        examples=[[{"role": "user", "content": "Hola"}, {"role": "assistant", "content": "¡Hola! ¿En qué te ayudo?"}]],
    )


def obtener_servicio_chat() -> chat.ServicioChat:
    """Servicio del chat. Es una dependencia para poder reemplazarla en las pruebas."""
    try:
        return chat.obtener_servicio()
    except chat.ErrorConfiguracionChat as error:
        raise HTTPException(status_code=503, detail=str(error))


@lru_cache
def obtener_almacen() -> Almacen:
    """Almacén de votos (SQLite). Es una dependencia para poder cambiarla en las pruebas."""
    return Almacen()


@lru_cache
def _catalogo() -> list[dict]:
    """Carga el CSV del catálogo una sola vez y lo guarda en memoria."""
    return cat.cargar_catalogo()


@lru_cache
def _equivalencias() -> dict[str, dict]:
    """Carga la tabla de equivalencias una sola vez (validada contra el catálogo)."""
    return clasificador.cargar_equivalencias(catalogo=_catalogo())


@app.get("/", include_in_schema=False)
def inicio():
    """La raíz redirige a la documentación interactiva."""
    return RedirectResponse(url="/docs")


@app.get("/salud")
def salud() -> dict:
    """Comprueba que el servicio está encendido."""
    return {"estado": "ok"}


@app.get("/catalogo")
def listar_catalogo(categoria: str | None = None) -> dict:
    """Lista los alimentos; se puede filtrar con ?categoria=proteina."""
    alimentos = _catalogo()
    if categoria is not None:
        try:
            categoria = validar_categoria(categoria)
        except ErrorValidacion as error:
            raise HTTPException(status_code=422, detail=str(error))
        alimentos = cat.filtrar_por_categoria(alimentos, categoria)
    return {"total": len(alimentos), "alimentos": alimentos}


@app.get("/catalogo/{nombre}")
def obtener_alimento(nombre: str) -> dict:
    """Devuelve un alimento por su nombre (ej. /catalogo/Quinua)."""
    alimento = cat.buscar_alimento(_catalogo(), nombre)
    if alimento is None:
        raise HTTPException(status_code=404, detail=f"No existe el alimento '{nombre}'.")
    return alimento


@app.post("/clasificar")
async def clasificar(
    foto: UploadFile = File(..., description="Foto JPG o PNG del alimento"),
    predictor: clasificador.Predictor = Depends(clasificador.obtener_predictor),
) -> dict:
    """Recibe una foto, identifica el alimento y lo enlaza con el catálogo."""
    # Se lee un byte de más que el máximo: así detectamos fotos demasiado grandes
    # sin cargar archivos enormes en memoria.
    maximo_bytes = config.TAMANO_MAX_IMAGEN_MB * 1024 * 1024
    contenido = await foto.read(maximo_bytes + 1)
    try:
        return clasificador.clasificar_imagen(
            contenido, foto.content_type, predictor, _catalogo(), _equivalencias()
        )
    except ErrorValidacion as error:
        raise HTTPException(status_code=422, detail=str(error))


@app.post("/recomendar")
def recomendar(entrada: EntradaRecomendacion, almacen: Almacen = Depends(obtener_almacen)) -> dict:
    """Arma el menú semanal de 21 comidas dentro del presupuesto, con la lista de compras.

    Si se envía "usuario_id", el menú se adapta a sus "me gusta / no me gusta".
    Sin "usuario_id" funciona igual que antes (sin personalización).
    """
    try:
        usuario = None
        gustos = None
        votos: dict[str, str] = {}
        if entrada.usuario_id is not None:
            usuario = validar_usuario_id(entrada.usuario_id)
            votos = almacen.obtener_votos(usuario)
            gustos = preferencias.calcular_preferencias(_catalogo(), votos)
        menu = recomendador.generar_menu(
            _catalogo(), entrada.presupuesto, entrada.personas, preferencias=gustos
        )
    except ErrorValidacion as error:  # incluye "presupuesto insuficiente"
        raise HTTPException(status_code=422, detail=str(error))
    if usuario is not None:
        menu["personalizacion"] = {"usuario_id": usuario, "votos_usados": len(votos)}
    return menu


# ---------------------------------------------------------------------------
# Preferencias del usuario ("me gusta / no me gusta")
# ---------------------------------------------------------------------------
@app.post("/feedback")
def registrar_feedback(entrada: EntradaVoto, almacen: Almacen = Depends(obtener_almacen)) -> dict:
    """Registra un voto. Si el usuario ya había votado ese alimento, el nuevo voto lo reemplaza."""
    try:
        usuario = validar_usuario_id(entrada.usuario_id)
        alimento = preferencias.resolver_alimento(_catalogo(), entrada.alimento)
        voto = validar_voto(entrada.voto)
    except ErrorValidacion as error:
        raise HTTPException(status_code=422, detail=str(error))
    total = almacen.registrar_voto(usuario, alimento, voto)
    return {"usuario_id": usuario, "alimento": alimento, "voto": voto, "total_votos": total}


@app.get("/preferencias/{usuario_id}")
def ver_preferencias(usuario_id: str, almacen: Almacen = Depends(obtener_almacen)) -> dict:
    """Muestra los votos de un usuario, qué alimentos recomendaría más y menos, y su historial."""
    try:
        usuario = validar_usuario_id(usuario_id)
    except ErrorValidacion as error:
        raise HTTPException(status_code=422, detail=str(error))
    votos = almacen.obtener_votos(usuario)
    gustos = preferencias.calcular_preferencias(_catalogo(), votos)
    destacados = preferencias.resumir_preferencias(_catalogo(), gustos) if gustos else {
        "mas_recomendados": [],
        "menos_recomendados": [],
    }
    return {
        "usuario_id": usuario,
        "total_votos": len(votos),
        "me_gusta": sorted(n for n, v in votos.items() if v == config.VOTO_ME_GUSTA),
        "no_me_gusta": sorted(n for n, v in votos.items() if v == config.VOTO_NO_ME_GUSTA),
        **destacados,
        "historial": almacen.obtener_historial(usuario),
    }


@app.delete("/feedback/{usuario_id}")
def reiniciar_feedback(usuario_id: str, almacen: Almacen = Depends(obtener_almacen)) -> dict:
    """Borra todos los votos de un usuario (útil para repetir la demostración)."""
    try:
        usuario = validar_usuario_id(usuario_id)
    except ErrorValidacion as error:
        raise HTTPException(status_code=422, detail=str(error))
    return {"usuario_id": usuario, "votos_borrados": almacen.reiniciar(usuario)}


# ---------------------------------------------------------------------------
# Chat con el asistente (modelo de Microsoft Foundry + catálogo)
# ---------------------------------------------------------------------------
@app.post("/chat")
def conversar(entrada: EntradaChat, servicio: chat.ServicioChat = Depends(obtener_servicio_chat)) -> dict:
    """Responde una pregunta de alimentación, compras o presupuesto usando el catálogo.

    Devuelve 503 si el chat no está configurado (.env) y 502 si Foundry no responde.
    """
    try:
        mensaje = validar_mensaje_chat(entrada.mensaje)
        historial = validar_historial_chat(entrada.historial)
    except ErrorValidacion as error:
        raise HTTPException(status_code=422, detail=str(error))
    try:
        return servicio.responder(mensaje, historial)
    except chat.ErrorChat as error:
        raise HTTPException(status_code=502, detail=str(error))
