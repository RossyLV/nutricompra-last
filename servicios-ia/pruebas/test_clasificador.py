"""Pruebas del clasificador con un modelo FALSO (no descarga nada) (Fase 2)."""
import io

import pytest
from PIL import Image

from app import catalogo as cat
from app import clasificador
from app.validacion import ErrorValidacion


@pytest.fixture(scope="module")
def catalogo():
    return cat.cargar_catalogo()


@pytest.fixture(scope="module")
def equivalencias(catalogo):
    return clasificador.cargar_equivalencias(catalogo=catalogo)


def foto(formato="PNG") -> bytes:
    """Crea en memoria una imagen de prueba de 32x32 píxeles."""
    buffer = io.BytesIO()
    Image.new("RGB", (32, 32), color=(200, 120, 40)).save(buffer, format=formato)
    return buffer.getvalue()


def predictor_falso(resultados):
    """Devuelve un predictor que siempre responde lo mismo."""
    return lambda imagen: resultados


def test_clasifica_pizza_y_enlaza_con_catalogo(catalogo, equivalencias):
    predictor = predictor_falso([
        {"label": "pizza", "score": 0.91},
        {"label": "lasagna", "score": 0.05},
        {"label": "ramen", "score": 0.02},
    ])
    r = clasificador.clasificar_imagen(foto(), "image/png", predictor, catalogo, equivalencias)
    principal = r["predicciones"][0]
    assert r["confiable"] is True
    assert principal["nombre"] == "Pizza"
    assert principal["categoria"] == "carbohidrato"
    assert principal["alimento"]["name"] == "Harina de trigo"
    assert principal["alimento"]["price_per_kg_ref"] > 0
    assert len(r["predicciones"]) == 3


def test_poca_confianza_avisa(catalogo, equivalencias):
    predictor = predictor_falso([{"label": "pizza", "score": 0.20}])
    r = clasificador.clasificar_imagen(foto(), "image/png", predictor, catalogo, equivalencias)
    assert r["confiable"] is False
    assert "No estoy seguro" in r["mensaje"]


def test_clase_sin_alimento_en_catalogo_devuelve_categoria_sin_alimento(catalogo, equivalencias):
    predictor = predictor_falso([{"label": "oysters", "score": 0.9}])
    principal = clasificador.clasificar_imagen(
        foto(), "image/png", predictor, catalogo, equivalencias
    )["predicciones"][0]
    assert principal["categoria"] == "proteina"
    assert principal["alimento"] is None


def test_clase_desconocida_no_rompe(catalogo, equivalencias):
    predictor = predictor_falso([{"label": "plato_inventado", "score": 0.9}])
    r = clasificador.clasificar_imagen(foto(), "image/png", predictor, catalogo, equivalencias)
    assert r["predicciones"][0]["categoria"] is None
    assert "tabla de equivalencias" in r["mensaje"]


def test_acepta_jpeg(catalogo, equivalencias):
    predictor = predictor_falso([{"label": "pizza", "score": 0.9}])
    r = clasificador.clasificar_imagen(foto("JPEG"), "image/jpeg", predictor, catalogo, equivalencias)
    assert r["confiable"] is True


def test_rechaza_tipo_no_permitido(catalogo, equivalencias):
    with pytest.raises(ErrorValidacion):
        clasificador.clasificar_imagen(
            foto(), "application/pdf", predictor_falso([]), catalogo, equivalencias
        )


def test_rechaza_archivo_que_no_es_imagen(catalogo, equivalencias):
    # Dice ser PNG pero el contenido es texto
    with pytest.raises(ErrorValidacion):
        clasificador.clasificar_imagen(
            b"esto no es una imagen", "image/png", predictor_falso([]), catalogo, equivalencias
        )


def test_rechaza_formato_real_no_permitido(catalogo, equivalencias):
    # Dice ser JPEG pero el contenido es un GIF
    with pytest.raises(ErrorValidacion):
        clasificador.clasificar_imagen(
            foto("GIF"), "image/jpeg", predictor_falso([]), catalogo, equivalencias
        )


def test_rechaza_imagen_demasiado_grande(catalogo, equivalencias):
    seis_megas = b"0" * (6 * 1024 * 1024)
    with pytest.raises(ErrorValidacion):
        clasificador.clasificar_imagen(
            seis_megas, "image/png", predictor_falso([]), catalogo, equivalencias
        )
