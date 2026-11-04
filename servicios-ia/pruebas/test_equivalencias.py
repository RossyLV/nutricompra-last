"""Pruebas de la tabla de equivalencias Food-101 -> categoría -> catálogo (Fase 2)."""
import pytest

from app import catalogo as cat
from app import clasificador, config


@pytest.fixture(scope="module")
def catalogo():
    return cat.cargar_catalogo()


@pytest.fixture(scope="module")
def equivalencias(catalogo):
    # cargar_equivalencias ya valida: categorías, alimentos existentes y coherencia
    return clasificador.cargar_equivalencias(catalogo=catalogo)


def test_hay_101_clases_de_food101(equivalencias):
    assert len(equivalencias) == 101


def test_todas_las_categorias_son_validas(equivalencias):
    assert all(f["app_category"] in config.CATEGORIAS_CATALOGO for f in equivalencias.values())


def test_las_cinco_categorias_del_balance_estan_representadas(equivalencias):
    usadas = {f["app_category"] for f in equivalencias.values()}
    assert set(config.CATEGORIAS_APP) <= usadas


def test_alimento_enlazado_existe_y_coincide_en_categoria(equivalencias, catalogo):
    for clase, fila in equivalencias.items():
        nombre = fila["alimento_catalogo"]
        if nombre:
            alimento = cat.buscar_alimento(catalogo, nombre)
            assert alimento is not None, clasificar_error(clase)
            assert alimento["app_category"] == fila["app_category"], clasificar_error(clase)


def clasificar_error(clase):
    return f"Problema en la clase '{clase}'"


def test_normalizar_etiqueta():
    assert clasificador.normalizar_etiqueta("Apple Pie") == "apple_pie"
    assert clasificador.normalizar_etiqueta(" french-fries ") == "french_fries"


def test_tabla_con_categoria_invalida_da_error(tmp_path, catalogo):
    mala = tmp_path / "mala.csv"
    mala.write_text(
        "clase_food101,nombre_es,app_category,alimento_catalogo\npizza,Pizza,postre,\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        clasificador.cargar_equivalencias(mala, catalogo)


def test_tabla_con_alimento_inexistente_da_error(tmp_path, catalogo):
    mala = tmp_path / "mala.csv"
    mala.write_text(
        "clase_food101,nombre_es,app_category,alimento_catalogo\npizza,Pizza,carbohidrato,Marciano\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        clasificador.cargar_equivalencias(mala, catalogo)
