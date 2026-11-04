"""Pruebas de los endpoints de la API (Fases 1 y 2)."""
import io

from fastapi.testclient import TestClient
from PIL import Image

from app import clasificador
from app.main import app

cliente = TestClient(app)


def foto_png() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (32, 32), color=(10, 200, 30)).save(buffer, format="PNG")
    return buffer.getvalue()


def usar_predictor_falso(resultados):
    """Reemplaza el modelo real por uno falso, solo para las pruebas."""
    app.dependency_overrides[clasificador.obtener_predictor] = lambda: (lambda imagen: resultados)


def test_salud():
    respuesta = cliente.get("/salud")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok"}


def test_listar_catalogo_completo():
    assert cliente.get("/catalogo").json()["total"] == 78


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


def test_clasificar_foto_valida():
    usar_predictor_falso([{"label": "guacamole", "score": 0.88}])
    try:
        respuesta = cliente.post("/clasificar", files={"foto": ("plato.png", foto_png(), "image/png")})
    finally:
        app.dependency_overrides.clear()
    assert respuesta.status_code == 200
    principal = respuesta.json()["predicciones"][0]
    assert principal["categoria"] == "fruta"
    assert principal["alimento"]["name"] == "Palta"


def test_clasificar_archivo_no_imagen_devuelve_422():
    usar_predictor_falso([])
    try:
        respuesta = cliente.post("/clasificar", files={"foto": ("nota.png", b"hola", "image/png")})
    finally:
        app.dependency_overrides.clear()
    assert respuesta.status_code == 422


def test_clasificar_formato_no_permitido_devuelve_422():
    usar_predictor_falso([])
    try:
        respuesta = cliente.post("/clasificar", files={"foto": ("a.pdf", b"%PDF", "application/pdf")})
    finally:
        app.dependency_overrides.clear()
    assert respuesta.status_code == 422


def test_recomendar_menu_valido():
    respuesta = cliente.post("/recomendar", json={"presupuesto": 200, "personas": 4})
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert len(datos["comidas"]) == 21
    assert datos["costo_total"] <= 200


def test_recomendar_presupuesto_invalido_devuelve_422():
    respuesta = cliente.post("/recomendar", json={"presupuesto": -10, "personas": 4})
    assert respuesta.status_code == 422
    assert "mayor que 0" in respuesta.json()["detail"]


def test_recomendar_presupuesto_insuficiente_devuelve_422():
    respuesta = cliente.post("/recomendar", json={"presupuesto": 40, "personas": 4})
    assert respuesta.status_code == 422
    assert "al menos" in respuesta.json()["detail"]
