"""Pruebas del endpoint POST /chat (Fase 5). Usan un servicio falso: no gastan crédito."""
import pytest
from fastapi.testclient import TestClient

from app import chat, config, main


class ServicioFalso:
    def __init__(self, error=None):
        self.error, self.llamadas = error, []

    def responder(self, mensaje, historial):
        self.llamadas.append((mensaje, historial))
        if self.error:
            raise self.error
        return {"respuesta": "Respuesta de prueba", "modelo": "falso"}


@pytest.fixture
def servicio():
    return ServicioFalso()


@pytest.fixture
def cliente(servicio):
    main.app.dependency_overrides[main.obtener_servicio_chat] = lambda: servicio
    yield TestClient(main.app)
    main.app.dependency_overrides.pop(main.obtener_servicio_chat, None)


def test_chat_responde(cliente, servicio):
    r = cliente.post("/chat", json={"mensaje": "  ¿Qué tiene hierro?  "})
    assert r.status_code == 200
    assert r.json() == {"respuesta": "Respuesta de prueba", "modelo": "falso"}
    assert servicio.llamadas == [("¿Qué tiene hierro?", [])]


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
