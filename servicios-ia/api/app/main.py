"""API (FastAPI) de los servicios de IA de NutriCompra.

Expone el catálogo y la clasificación de fotos para que el prototipo y el
dashboard los consuman. Más adelante se agrega la recomendación de menús.
"""
from functools import lru_cache
from typing import Any

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app import catalogo as cat
from app import clasificador, config, recomendador
from app.validacion import ErrorValidacion, validar_categoria

app = FastAPI(
    title="NutriCompra Inteligente - Servicios de IA",
    description="Catálogo, clasificación de alimentos y recomendación de menús.",
    version="0.3.0",
)


class EntradaRecomendacion(BaseModel):
    """Datos para armar el menú. Se declaran como "Any" a propósito: la validación
    (y sus mensajes en español) la hace app.validacion, no pydantic."""

    presupuesto: Any = Field(..., description="Presupuesto semanal en soles (> 0)", examples=[200])
    personas: Any = Field(..., description="Personas del hogar (>= 1)", examples=[4])


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
def recomendar(entrada: EntradaRecomendacion) -> dict:
    """Arma el menú semanal de 21 comidas dentro del presupuesto, con la lista de compras."""
    try:
        return recomendador.generar_menu(_catalogo(), entrada.presupuesto, entrada.personas)
    except ErrorValidacion as error:  # incluye "presupuesto insuficiente"
        raise HTTPException(status_code=422, detail=str(error))
