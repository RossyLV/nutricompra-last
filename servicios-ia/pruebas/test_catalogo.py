"""Pruebas de la lectura y consulta del catálogo (Fase 1)."""
import pytest

from app import catalogo as cat
from app import config


@pytest.fixture(scope="module")
def alimentos():
    return cat.cargar_catalogo()


def test_catalogo_tiene_78_alimentos(alimentos):
    assert len(alimentos) == 78


def test_nombres_son_unicos(alimentos):
    nombres = [a["name"] for a in alimentos]
    assert len(nombres) == len(set(nombres))


def test_todas_las_categorias_app_son_validas(alimentos):
    assert all(a["app_category"] in config.CATEGORIAS_CATALOGO for a in alimentos)


def test_precios_son_positivos(alimentos):
    assert all(a["price_per_kg_ref"] > 0 for a in alimentos)


def test_dato_vacio_queda_como_none_y_no_como_cero(alimentos):
    # El arroz blanco no trae fibra en la TPCA: debe ser None, nunca 0
    arroz = cat.buscar_alimento(alimentos, "Arroz blanco")
    assert arroz["fiber_g"] is None
    # El aceite sí tiene proteína medida en 0: debe seguir siendo 0
    aceite = cat.buscar_alimento(alimentos, "Aceite vegetal")
    assert aceite["protein_g"] == 0.0


def test_buscar_alimento_ignora_mayusculas(alimentos):
    assert cat.buscar_alimento(alimentos, "quinua")["name"] == "Quinua"


def test_buscar_alimento_inexistente(alimentos):
    assert cat.buscar_alimento(alimentos, "Pizza") is None


def test_filtrar_por_categoria(alimentos):
    lacteos = cat.filtrar_por_categoria(alimentos, "lacteo")
    assert len(lacteos) == 6
    assert all(a["app_category"] == "lacteo" for a in lacteos)


def test_obtener_precio(alimentos):
    assert cat.obtener_precio(alimentos, "Papa blanca") == 2.8
    assert cat.obtener_precio(alimentos, "Pizza") is None


def test_csv_con_columna_faltante_da_error(tmp_path):
    malo = tmp_path / "malo.csv"
    malo.write_text("name,category\nArroz,Cereales\n", encoding="utf-8")
    with pytest.raises(ValueError):
        cat.cargar_catalogo(malo)
