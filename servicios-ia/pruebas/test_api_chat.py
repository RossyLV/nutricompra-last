"""Pruebas del endpoint POST /chat (Fase 5). Usan un servicio falso: no gastan crédito."""
import pytest
from fastapi.testclient import TestClient

from app import chat, config, main
from app.almacen import Almacen


class ServicioFalso:
    def __init__(self, error=None):
        self.error, self.llamadas = error, []

    def responder(self, mensaje, historial, perfil=""):
        self.llamadas.append((mensaje, historial, perfil))
        if self.error:
            raise self.error
        return {"respuesta": "Respuesta de prueba", "modelo": "falso"}


@pytest.fixture
def servicio():
    return ServicioFalso()


@pytest.fixture
def cliente(servicio, tmp_path):
    main.app.dependency_overrides[main.obtener_servicio_chat] = lambda: servicio
    main.app.dependency_overrides[main.obtener_almacen] = lambda: Almacen(tmp_path / "chat.db")
    yield TestClient(main.app)
    main.app.dependency_overrides.pop(main.obtener_servicio_chat, None)
    main.app.dependency_overrides.pop(main.obtener_almacen, None)


def test_chat_responde(cliente, servicio):
    r = cliente.post("/chat", json={"mensaje": "  ¿Qué tiene hierro?  "})
    assert r.status_code == 200
    assert r.json() == {"respuesta": "Respuesta de prueba", "modelo": "falso"}
    assert servicio.llamadas == [("¿Qué tiene hierro?", [], "")]  # sin usuario: sin perfil


def test_chat_pasa_el_historial_al_servicio(cliente, servicio):
    historial = [{"role": "user", "content": "Hola"}, {"role": "assistant", "content": "¡Hola!"}]
    cliente.post("/chat", json={"mensaje": "¿Y la quinua?", "historial": historial})
    assert servicio.llamadas[0][1] == historial


@pytest.mark.parametrize("cuerpo", [
    {"mensaje": ""},
    {"mensaje": 5},
    {"mensaje": "x" * (config.CHAT_MENSAJE_MAX_LARGO + 1)},
    {"mensaje": "Hola", "historial": "texto"},
    {"mensaje": "Hola", "historial": [{"role": "system", "content": "x"}]},
])
def test_chat_con_datos_invalidos_da_422_en_espanol(cliente, servicio, cuerpo):
    r = cliente.post("/chat", json=cuerpo)
    assert r.status_code == 422
    assert isinstance(r.json()["detail"], str)
    assert servicio.llamadas == []  # no se gastó ninguna consulta


def test_chat_con_fallo_de_foundry_da_502(cliente, servicio):
    servicio.error = chat.ErrorChat("No se pudo obtener respuesta del asistente.")
    r = cliente.post("/chat", json={"mensaje": "Hola"})
    assert r.status_code == 502
    assert "asistente" in r.json()["detail"]


def test_chat_sin_configurar_da_503_y_dice_que_falta(monkeypatch):
    monkeypatch.setattr(config, "CHAT_CLAVE", "")
    monkeypatch.setattr(config, "CHAT_ID_INDICE", "")
    r = TestClient(main.app).post("/chat", json={"mensaje": "Hola"})
    assert r.status_code == 503
    assert "AZURE_OPENAI_API_KEY" in r.json()["detail"]


# --- Personalización ------------------------------------------------------
def _nombres(categoria, cantidad):
    return [a["name"] for a in main._catalogo() if a["app_category"] == categoria][:cantidad]


def test_chat_con_usuario_sin_votos_responde_igual_y_marca_la_personalizacion(cliente, servicio):
    r = cliente.post("/chat", json={"mensaje": "Hola", "usuario_id": "nuevo"})
    assert r.status_code == 200
    assert r.json()["personalizacion"] == {"usuario_id": "nuevo", "votos_usados": 0}
    assert servicio.llamadas[0][2] == ""  # sin votos ni datos: no hay perfil que contar


def test_chat_con_votos_le_pasa_el_perfil_al_modelo(cliente, servicio):
    gusta, no_gusta = _nombres("proteina", 2)
    usuario = "usuario_secreto_77"
    cliente.post("/feedback", json={"usuario_id": usuario, "alimento": gusta, "voto": "me_gusta"})
    cliente.post("/feedback", json={"usuario_id": usuario, "alimento": no_gusta, "voto": "no_me_gusta"})
    r = cliente.post("/chat", json={"mensaje": "¿Qué ceno?", "usuario_id": usuario, "presupuesto": 60, "personas": 4})
    assert r.json()["personalizacion"] == {"usuario_id": usuario, "votos_usados": 2}
    perfil = servicio.llamadas[0][2]
    assert f"Le gustan: {gusta}" in perfil and f"No le gustan: {no_gusta}" in perfil
    assert "Hogar: 4 personas" in perfil and "S/ 60.00" in perfil
    assert usuario not in perfil  # el identificador del usuario nunca llega al modelo


def test_chat_con_presupuesto_y_sin_usuario_tambien_personaliza(cliente, servicio):
    r = cliente.post("/chat", json={"mensaje": "Hola", "presupuesto": 100, "personas": 2})
    assert r.status_code == 200
    assert "personalizacion" not in r.json()
    assert "S/ 100.00" in servicio.llamadas[0][2]


@pytest.mark.parametrize("extra", [
    {"usuario_id": "a b"}, {"usuario_id": 5}, {"presupuesto": -1}, {"presupuesto": "mucho"},
    {"personas": 0}, {"personas": 2.5},
])
def test_chat_con_datos_de_perfil_invalidos_da_422(cliente, servicio, extra):
    r = cliente.post("/chat", json={"mensaje": "Hola", **extra})
    assert r.status_code == 422
    assert isinstance(r.json()["detail"], str)
    assert servicio.llamadas == []
