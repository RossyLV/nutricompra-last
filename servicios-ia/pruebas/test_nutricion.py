"""Pruebas de los cálculos nutricionales (Fase 3)."""
import pytest

from app import catalogo as cat
from app import config
from app.nutricion import aporte_porcion, porcion_g, puntaje_dia, puntaje_nutriente, sumar_aportes


@pytest.fixture(scope="module")
def catalogo():
    return cat.cargar_catalogo()


REGLA_MINIMO = {"tipo": "minimo", "min": 50}
REGLA_RANGO = {"tipo": "rango", "min": 1800, "max": 2400}


def test_minimo_alcanzado_da_1():
    assert puntaje_nutriente(80, REGLA_MINIMO) == 1.0


def test_minimo_a_la_mitad_da_medio():
    assert puntaje_nutriente(25, REGLA_MINIMO) == pytest.approx(0.5)


def test_rango_dentro_da_1():
    assert puntaje_nutriente(2000, REGLA_RANGO) == 1.0


def test_rango_por_debajo_baja():
    assert puntaje_nutriente(900, REGLA_RANGO) == pytest.approx(0.5)


def test_rango_por_encima_baja():
    assert 0 < puntaje_nutriente(3000, REGLA_RANGO) < 1


def test_puntaje_dia_perfecto_y_nulo():
    perfecto = {n: 10_000.0 if config.REQUERIMIENTOS[n]["tipo"] == "minimo" else
                (config.REQUERIMIENTOS[n]["min"] + config.REQUERIMIENTOS[n]["max"]) / 2
                for n in config.NUTRIENTES_BALANCE}
    assert puntaje_dia(perfecto) == pytest.approx(1.0)
    assert puntaje_dia({n: 0.0 for n in config.NUTRIENTES_BALANCE}) == 0.0


def test_dato_faltante_no_se_convierte_en_cero(catalogo):
    # El atún no trae calcio ni hierro en la TPCA
    atun = cat.buscar_alimento(catalogo, "Atún")
    aporte = aporte_porcion(atun)
    assert aporte["calcium_mg"] is None
    totales, faltantes = sumar_aportes([aporte])
    assert faltantes["calcium_mg"] == 1
    assert faltantes["protein_g"] == 0


def test_porciones_especiales(catalogo):
    assert porcion_g(cat.buscar_alimento(catalogo, "Queso fresco")) == 40
    assert porcion_g(cat.buscar_alimento(catalogo, "Lentejas")) == 80
    assert porcion_g(cat.buscar_alimento(catalogo, "Quinua")) == config.PORCIONES_G["carbohidrato"]


def test_aporte_se_escala_a_la_porcion(catalogo):
    pollo = cat.buscar_alimento(catalogo, "Pollo")  # 119 kcal por 100 g, porción de 120 g
    assert aporte_porcion(pollo)["energy_kcal"] == pytest.approx(119 * 1.2)
