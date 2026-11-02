"""API (FastAPI) de los servicios de IA de NutriCompra.

Expone el catálogo para que el prototipo y el dashboard lo consuman.
Más adelante se agregan aquí la clasificación y la recomendación.
"""
from functools import lru_cache

from fastapi import FastAPI, HTTPException

from app import catalogo as cat
from app.validacion import ErrorValidacion, validar_categoria

app = FastAPI(
    title="NutriCompra Inteligente - Servicios de IA",
    description="Catálogo, clasificación de alimentos y recomendación de menús.",
    version="0.1.0",
)


@lru_cache
def _catalogo() -> list[dict]:
    """Carga el CSV una sola vez y lo guarda en memoria."""
    return cat.cargar_catalogo()


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
