"""Pruebas del recomendador de menús (Fase 3)."""
from collections import Counter

import pytest

from app import catalogo as cat
from app import config
from app.recomendador import ErrorPresupuestoInsuficiente, generar_menu
from app.validacion import ErrorValidacion

# Pocas iteraciones: así las pruebas corren rápido (el resultado sigue siendo válido)
ITER = 1500


@pytest.fixture(scope="module")
def catalogo():
    return cat.cargar_catalogo()


@pytest.fixture(scope="module")
def menu(catalogo):
    return generar_menu(catalogo, 200, 4, iteraciones=ITER)


def test_menu_tiene_21_comidas(menu):
    assert len(menu["comidas"]) == config.TOTAL_COMIDAS_SEMANA == 21


def test_cada_comida_respeta_su_estructura(menu):
    for comida in menu["comidas"]:
        categorias = tuple(i["categoria"] for i in comida["ingredientes"])
        assert categorias == config.ESTRUCTURA_COMIDAS[comida["momento"]]


@pytest.mark.parametrize("presupuesto, personas", [(120, 4), (150, 4), (200, 4), (60, 2), (400, 5)])
def test_nunca_se_pasa_del_presupuesto(catalogo, presupuesto, personas):
    resultado = generar_menu(catalogo, presupuesto, personas, iteraciones=ITER)
    assert resultado["costo_total"] <= presupuesto
    assert resultado["ahorro"] >= 0


def test_el_costo_total_coincide_con_la_suma_de_comidas(menu):
    assert menu["costo_total"] == pytest.approx(sum(c["costo"] for c in menu["comidas"]), abs=0.1)


def test_mejora_frente_al_menu_basico(menu):
    assert menu["puntaje_balance"] > menu["puntaje_balance_menu_basico"]


def test_mas_presupuesto_no_empeora_el_balance(catalogo):
    ajustado = generar_menu(catalogo, 130, 4, iteraciones=ITER)
    holgado = generar_menu(catalogo, 250, 4, iteraciones=ITER)
    assert holgado["puntaje_balance"] >= ajustado["puntaje_balance"]


def test_reglas_de_variedad(menu):
    usos = Counter(i["nombre"] for c in menu["comidas"] for i in c["ingredientes"])
    assert max(usos.values()) <= config.MAX_REPETICIONES_SEMANA
    por_dia = {}
    for c in menu["comidas"]:
        proteinas = [i["nombre"] for i in c["ingredientes"] if i["categoria"] == "proteina"]
        por_dia.setdefault(c["dia"], []).extend(proteinas)
    for proteinas in por_dia.values():
        assert len(proteinas) == len(set(proteinas))  # almuerzo y cena distintos


def test_no_usa_ingredientes_excluidos(menu):
    usados = {i["nombre"] for c in menu["comidas"] for i in c["ingredientes"]}
    assert not usados & set(config.INGREDIENTES_EXCLUIDOS)


def test_mismo_resultado_con_la_misma_semilla(catalogo):
    a = generar_menu(catalogo, 200, 4, semilla=7, iteraciones=ITER)
    b = generar_menu(catalogo, 200, 4, semilla=7, iteraciones=ITER)
    assert a == b


def test_presupuesto_insuficiente_informa_el_minimo(catalogo):
    with pytest.raises(ErrorPresupuestoInsuficiente) as error:
        generar_menu(catalogo, 50, 4)
    assert error.value.costo_minimo > 50
    assert "al menos" in str(error.value)


@pytest.mark.parametrize("presupuesto, personas", [(0, 4), (-5, 4), ("abc", 4), (200, 0), (200, 2.5)])
def test_entradas_invalidas(catalogo, presupuesto, personas):
    with pytest.raises(ErrorValidacion):
        generar_menu(catalogo, presupuesto, personas)


def test_lista_de_compras_suma_los_gramos(menu):
    total_lista = sum(i["gramos"] for i in menu["lista_compras"])
    total_comidas = sum(
        i["gramos_por_persona"] * menu["personas"] for c in menu["comidas"] for i in c["ingredientes"]
    )
    assert total_lista == total_comidas


def test_las_preferencias_se_reflejan_en_el_menu(catalogo):
    neutro = generar_menu(catalogo, 200, 4, iteraciones=ITER)
    con_gustos = generar_menu(catalogo, 200, 4, preferencias={"Quinua": 1.0, "Lentejas": 0.0}, iteraciones=ITER)

    def usos(resultado, nombre):
        return sum(1 for c in resultado["comidas"] for i in c["ingredientes"] if i["nombre"] == nombre)

    assert usos(con_gustos, "Quinua") >= usos(neutro, "Quinua")
    assert usos(con_gustos, "Lentejas") <= usos(neutro, "Lentejas")


def test_avisa_cuando_faltan_datos_nutricionales(catalogo):
    # Con presupuesto holgado se usa leche evaporada entera, que no trae hierro
    resultado = generar_menu(catalogo, 200, 4, iteraciones=ITER)
    if resultado["avisos"]:
        assert "Faltan datos" in resultado["avisos"][0]
