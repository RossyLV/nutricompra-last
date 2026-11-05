"""Pruebas de los endpoints de preferencias (Fase 4).

Usan el catálogo real del proyecto y una base de datos temporal (no tocan
datos/preferencias.db). Los nombres de alimentos se toman del propio catálogo,
así las pruebas no dependen de que exista un alimento en particular.
"""
import pytest
from fastapi.testclient import TestClient

from app import main
from app.almacen import Almacen


@pytest.fixture
def cliente(tmp_path):
    """Cliente de pruebas con una base de datos temporal."""
    main.app.dependency_overrides[main.obtener_almacen] = lambda: Almacen(tmp_path / "api.db")
    yield TestClient(main.app)
    main.app.dependency_overrides.pop(main.obtener_almacen, None)


def _nombres(categoria: str, cantidad: int) -> list[str]:
    """Nombres reales de alimentos de una categoría del catálogo."""
    return [a["name"] for a in main._catalogo() if a["app_category"] == categoria][:cantidad]


def _votar(cliente, usuario, alimento, voto="me_gusta"):
    return cliente.post("/feedback", json={"usuario_id": usuario, "alimento": alimento, "voto": voto})


def test_registrar_un_voto(cliente):
    alimento = _nombres("proteina", 1)[0]
    r = _votar(cliente, "ana", alimento.lower())  # sin importar mayúsculas
    assert r.status_code == 200
    assert r.json() == {"usuario_id": "ana", "alimento": alimento, "voto": "me_gusta", "total_votos": 1}


def test_un_voto_nuevo_reemplaza_al_anterior(cliente):
    alimento = _nombres("proteina", 1)[0]
    _votar(cliente, "ana", alimento, "me_gusta")
    r = _votar(cliente, "ana", alimento, "no_me_gusta")
    assert r.json()["total_votos"] == 1
    datos = cliente.get("/preferencias/ana").json()
    assert datos["no_me_gusta"] == [alimento] and datos["me_gusta"] == []


@pytest.mark.parametrize("cuerpo", [
    {"usuario_id": "ana", "alimento": "NoExiste", "voto": "me_gusta"},
    {"usuario_id": "ana", "alimento": "Quinua", "voto": "quizas"},
    {"usuario_id": "a b", "alimento": "Quinua", "voto": "me_gusta"},
    {"usuario_id": "", "alimento": "Quinua", "voto": "me_gusta"},
    {"usuario_id": "ana", "alimento": 5, "voto": "me_gusta"},
])
def test_votos_invalidos_dan_422_en_espanol(cliente, cuerpo):
    r = cliente.post("/feedback", json=cuerpo)
    assert r.status_code == 422
    assert isinstance(r.json()["detail"], str)  # mensaje en texto, no el formato de pydantic


def test_ver_preferencias_de_un_usuario_nuevo(cliente):
    datos = cliente.get("/preferencias/nuevo").json()
    assert datos["total_votos"] == 0
    assert datos["mas_recomendados"] == [] and datos["historial"] == []


def test_ver_preferencias_con_votos(cliente):
    favorito, otro = _nombres("proteina", 2)
    _votar(cliente, "ana", favorito, "me_gusta")
    _votar(cliente, "ana", otro, "no_me_gusta")
    datos = cliente.get("/preferencias/ana").json()
    assert datos["total_votos"] == 2
    assert datos["me_gusta"] == [favorito] and datos["no_me_gusta"] == [otro]
    assert len(datos["mas_recomendados"]) > 0
    assert [h["numero"] for h in datos["historial"]] == [1, 2]


def test_usuario_invalido_en_la_ruta(cliente):
    assert cliente.get("/preferencias/a%20b").status_code == 422
    assert cliente.delete("/feedback/a%20b").status_code == 422


def test_reiniciar_borra_los_votos(cliente):
    _votar(cliente, "ana", _nombres("proteina", 1)[0])
    r = cliente.delete("/feedback/ana")
    assert r.json() == {"usuario_id": "ana", "votos_borrados": 1}
    assert cliente.get("/preferencias/ana").json()["total_votos"] == 0


def test_recomendar_sin_usuario_sigue_igual_que_antes(cliente):
    r = cliente.post("/recomendar", json={"presupuesto": 200, "personas": 4})
    assert r.status_code == 200
    assert "personalizacion" not in r.json()
    assert len(r.json()["comidas"]) == 21


def test_recomendar_con_usuario_sin_votos_es_igual_al_menu_base(cliente):
    base = cliente.post("/recomendar", json={"presupuesto": 200, "personas": 4}).json()
    r = cliente.post("/recomendar", json={"presupuesto": 200, "personas": 4, "usuario_id": "nuevo"}).json()
    assert r["personalizacion"] == {"usuario_id": "nuevo", "votos_usados": 0}
    assert r["comidas"] == base["comidas"]


def test_recomendar_con_votos_usa_la_personalizacion(cliente):
    for nombre in _nombres("proteina", 3):
        _votar(cliente, "ana", nombre, "me_gusta")
    r = cliente.post("/recomendar", json={"presupuesto": 200, "personas": 4, "usuario_id": "ana"})
    assert r.status_code == 200
    assert r.json()["personalizacion"]["votos_usados"] == 3
    assert r.json()["costo_total"] <= 200


def test_recomendar_con_usuario_invalido(cliente):
    r = cliente.post("/recomendar", json={"presupuesto": 200, "personas": 4, "usuario_id": "a b"})
    assert r.status_code == 422
