"""Pruebas del chat (Fase 5).

No se conectan a Foundry: usan un "cliente falso" que imita al real, así las pruebas
son gratis, rápidas y funcionan sin internet ni claves.
"""
import sys
from types import SimpleNamespace

import pytest

from app import chat, config
from app.validacion import ErrorValidacion, validar_historial_chat, validar_mensaje_chat


class RespuestasFalsas:
    """Imita a cliente.responses: guarda lo que recibe y devuelve una salida fija o un error."""

    def __init__(self, salida="Respuesta de prueba", error=None):
        self.salida, self.error, self.llamadas = salida, error, []

    def create(self, **kwargs):
        self.llamadas.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(output_text=self.salida)


def _servicio(**kwargs):
    respuestas = RespuestasFalsas(**kwargs)
    return chat.ServicioChat(SimpleNamespace(responses=respuestas), "mi-despliegue", "vs_123"), respuestas


# --- ServicioChat ---------------------------------------------------------
def test_responder_devuelve_el_texto_y_el_modelo():
    servicio, _ = _servicio(salida="  Hola, soy NutriCompra  ")
    assert servicio.responder("Hola", []) == {"respuesta": "Hola, soy NutriCompra", "modelo": "mi-despliegue"}


def test_la_consulta_usa_el_catalogo_las_instrucciones_y_el_historial():
    servicio, respuestas = _servicio()
    historial = [{"role": "user", "content": "Hola"}, {"role": "assistant", "content": "¡Hola!"}]
    servicio.responder("¿Qué tiene hierro?", historial)
    llamada = respuestas.llamadas[0]
    assert llamada["model"] == "mi-despliegue"
    assert llamada["tools"] == [{"type": "file_search", "vector_store_ids": ["vs_123"]}]
    assert "SOLO el archivo del catálogo" in llamada["instructions"]
    assert llamada["input"] == [*historial, {"role": "user", "content": "¿Qué tiene hierro?"}]
    assert llamada["max_output_tokens"] == config.CHAT_MAX_TOKENS_SALIDA


def test_un_fallo_de_foundry_no_filtra_detalles_internos():
    secreto = "clave-super-secreta-123"
    servicio, _ = _servicio(error=RuntimeError(f"401 con {secreto}"))
    with pytest.raises(chat.ErrorChat) as info:
        servicio.responder("Hola", [])
    assert secreto not in str(info.value)
    assert "Intenta de nuevo" in str(info.value)


@pytest.mark.parametrize("salida", ["", "   ", None])
def test_una_respuesta_vacia_es_un_error(salida):
    servicio, _ = _servicio(salida=salida)
    with pytest.raises(chat.ErrorChat):
        servicio.responder("Hola", [])


# --- Configuración --------------------------------------------------------
@pytest.mark.parametrize("escrito, esperado", [
    ("https://mi-recurso.openai.azure.com/", "https://mi-recurso.openai.azure.com/openai/v1/"),
    ("https://mi-recurso.openai.azure.com", "https://mi-recurso.openai.azure.com/openai/v1/"),
    ("  https://mi-recurso.openai.azure.com/openai/v1  ", "https://mi-recurso.openai.azure.com/openai/v1/"),
    ("https://mi-recurso.openai.azure.com/openai/v1/", "https://mi-recurso.openai.azure.com/openai/v1/"),
])
def test_normalizar_endpoint(escrito, esperado):
    assert chat.normalizar_endpoint(escrito) == esperado


@pytest.mark.parametrize("malo", ["", "   ", None, 5, "http://inseguro.com", "mi-recurso.azure.com"])
def test_endpoint_invalido(malo):
    with pytest.raises(chat.ErrorConfiguracionChat):
        chat.normalizar_endpoint(malo)


def test_configuracion_incompleta_nombra_las_variables_pero_no_los_valores(monkeypatch):
    monkeypatch.setattr(config, "CHAT_ENDPOINT", "https://x.openai.azure.com/")
    monkeypatch.setattr(config, "CHAT_CLAVE", "")
    monkeypatch.setattr(config, "CHAT_ID_INDICE", "")
    with pytest.raises(chat.ErrorConfiguracionChat) as info:
        chat.obtener_servicio()
    mensaje = str(info.value)
    assert "AZURE_OPENAI_API_KEY" in mensaje and "ID_INDICE_CATALOGO" in mensaje
    assert "AZURE_OPENAI_ENDPOINT" not in mensaje  # ese sí está definido


def test_crear_cliente_no_exige_el_indice(monkeypatch):
    """Los scripts de herramientas necesitan crear el cliente antes de tener un índice."""
    monkeypatch.setattr(config, "CHAT_ENDPOINT", "https://x.openai.azure.com/")
    monkeypatch.setattr(config, "CHAT_CLAVE", "una-clave")
    monkeypatch.setattr(config, "CHAT_ID_INDICE", "")
    chat.verificar_configuracion(requiere_indice=False)  # no lanza error


def test_si_falta_la_libreria_openai_el_error_es_claro(monkeypatch):
    chat._crear_cliente.cache_clear()
    monkeypatch.setitem(sys.modules, "openai", None)  # hace que "import openai" falle
    with pytest.raises(chat.ErrorConfiguracionChat, match="openai"):
        chat._crear_cliente("https://x.openai.azure.com/", "clave")
    chat._crear_cliente.cache_clear()


# --- Lectura del .env -----------------------------------------------------
def test_cargar_env_lee_variables_ignora_comentarios_y_no_pisa_las_existentes(tmp_path, monkeypatch):
    archivo = tmp_path / ".env"
    archivo.write_text(
        "# comentario\n\nPRUEBA_A=uno\nPRUEBA_B = \"dos\" \nPRUEBA_C='tres'\nPRUEBA_D=a=b\nsin_igual\nPRUEBA_E=desde_archivo\n",
        encoding="utf-8",
    )
    for nombre in ("PRUEBA_A", "PRUEBA_B", "PRUEBA_C", "PRUEBA_D"):
        monkeypatch.delenv(nombre, raising=False)
    monkeypatch.setenv("PRUEBA_E", "ya_existia")
    config.cargar_env(archivo)
    import os
    assert (os.environ["PRUEBA_A"], os.environ["PRUEBA_B"], os.environ["PRUEBA_C"]) == ("uno", "dos", "tres")
    assert os.environ["PRUEBA_D"] == "a=b"
    assert os.environ["PRUEBA_E"] == "ya_existia"
    for nombre in ("PRUEBA_A", "PRUEBA_B", "PRUEBA_C", "PRUEBA_D"):
        monkeypatch.delenv(nombre, raising=False)


def test_cargar_env_sin_archivo_no_falla(tmp_path):
    config.cargar_env(tmp_path / "no_existe.env")


# --- Catálogo en texto ----------------------------------------------------
def _alimento(nombre, kcal=100.0, hierro=1.5, precio=4.0):
    return {
        "name": nombre, "category": "Cereales", "reference_amount": 100.0, "energy_kcal": kcal,
        "protein_g": 7.0, "carbohydrate_g": 70.0, "fat_g": 1.0, "fiber_g": 3.0, "sodium_mg": 5.0,
        "calcium_mg": 20.0, "iron_mg": hierro, "price_per_kg_ref": precio,
    }


def test_catalogo_a_texto_una_linea_por_alimento():
    texto = chat.catalogo_a_texto([_alimento("Kiwicha", kcal=351), _alimento("Quinua")])
    lineas = [x for x in texto.splitlines() if x.startswith("Alimento:")]
    assert len(lineas) == 2
    assert "Alimento: Kiwicha" in lineas[0] and "Energía: 351 kcal" in lineas[0]
    assert "Precio referencial: S/ 4.00 por kg" in lineas[0]


def test_el_dato_faltante_se_escribe_sin_dato_y_nunca_como_cero():
    texto = chat.catalogo_a_texto([_alimento("Raro", hierro=None, precio=None)])
    assert "Hierro: sin dato" in texto and "Precio referencial: sin dato" in texto
    assert "Hierro: 0" not in texto


def test_catalogo_a_texto_con_el_catalogo_real_del_proyecto():
    from app import catalogo
    alimentos = catalogo.cargar_catalogo()
    texto = chat.catalogo_a_texto(alimentos)
    assert len([x for x in texto.splitlines() if x.startswith("Alimento:")]) == len(alimentos)


# --- Validadores del chat -------------------------------------------------
def test_mensaje_valido_se_limpia():
    assert validar_mensaje_chat("  ¿Qué tiene hierro?  ") == "¿Qué tiene hierro?"


@pytest.mark.parametrize("malo", ["", "   ", None, 5, [], "x" * (config.CHAT_MENSAJE_MAX_LARGO + 1)])
def test_mensaje_invalido(malo):
    with pytest.raises(ErrorValidacion):
        validar_mensaje_chat(malo)


def test_historial_vacio_o_ausente():
    assert validar_historial_chat(None) == []
    assert validar_historial_chat([]) == []


def test_historial_valido_se_devuelve_limpio_sin_claves_extra():
    entrada = [{"role": "user", "content": "Hola", "extra": "x"}, {"role": "assistant", "content": "¡Hola!"}]
    assert validar_historial_chat(entrada) == [
        {"role": "user", "content": "Hola"},
        {"role": "assistant", "content": "¡Hola!"},
    ]


@pytest.mark.parametrize("malo", [
    "texto", {"role": "user"}, ["hola"], [{"role": "system", "content": "x"}],
    [{"role": "user", "content": ""}], [{"role": "user", "content": 5}], [{"content": "x"}],
    [{"role": "user", "content": "x" * (config.CHAT_HISTORIAL_MAX_LARGO + 1)}],
    [{"role": "user", "content": "x"}] * (config.CHAT_HISTORIAL_MAX_MENSAJES + 1),
])
def test_historial_invalido(malo):
    with pytest.raises(ErrorValidacion):
        validar_historial_chat(malo)
