"""Pruebas de los endpoints de la API (Fase 1)."""
from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


def test_salud():
    respuesta = cliente.get("/salud")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok"}


def test_listar_catalogo_completo():
    datos = cliente.get("/catalogo").json()
    assert datos["total"] == 78


def test_filtrar_por_categoria():
    datos = cliente.get("/catalogo", params={"categoria": "fruta"}).json()
    assert datos["total"] == 14


def test_categoria_invalida_devuelve_422():
    assert cliente.get("/catalogo", params={"categoria": "postre"}).status_code == 422


def test_obtener_alimento_con_espacios():
    respuesta = cliente.get("/catalogo/Leche fresca entera")
    assert respuesta.status_code == 200
    assert respuesta.json()["name"] == "Leche fresca entera"


def test_alimento_inexistente_devuelve_404():
    assert cliente.get("/catalogo/Pizza").status_code == 404
