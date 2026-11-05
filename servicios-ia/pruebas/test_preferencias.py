"""Pruebas del aprendizaje de preferencias (Fase 4)."""
import pytest

from app import config, preferencias, recomendador
from app.validacion import ErrorValidacion, validar_usuario_id, validar_voto


def _alimento(nombre, categoria, kcal, proteina, carbo, grasa, calcio, hierro, precio):
    """Un alimento mínimo con las columnas que usa el sistema."""
    return {
        "name": nombre, "category": "Prueba", "app_category": categoria,
        "reference_amount": 100.0, "energy_kcal": kcal, "protein_g": proteina,
        "carbohydrate_g": carbo, "fat_g": grasa, "fiber_g": 1.0, "sodium_mg": 1.0,
        "calcium_mg": calcio, "iron_mg": hierro, "price_per_kg_ref": precio,
    }


@pytest.fixture
def catalogo():
    """Catálogo pequeño: 8 alimentos por categoría, con valores distintos."""
    alimentos = []
    for i in range(8):
        alimentos.append(_alimento(f"Carbo{i}", "carbohidrato", 300 + 10 * i, 8, 60 + i, 1, 20, 2, 4 + i))
        alimentos.append(_alimento(f"Prote{i}", "proteina", 120 + 15 * i, 15 + i, 0, 3 + i, 20, 2 + i, 8 + 2 * i))
        alimentos.append(_alimento(f"Vege{i}", "vegetal", 20 + 3 * i, 1.5, 4, 0.2, 40, 1, 2 + i / 2))
        alimentos.append(_alimento(f"Fruta{i}", "fruta", 40 + 5 * i, 0.8, 11, 0.2, 10, 0.3, 3 + i / 2))
        alimentos.append(_alimento(f"Lacteo{i}", "lacteo", 60 + 10 * i, 3.5, 5, 3, 120, 0.1, 4 + i))
    return alimentos


def test_sin_votos_no_hay_preferencias(catalogo):
    assert preferencias.calcular_preferencias(catalogo, {}) == {}


def test_me_gusta_sube_y_no_me_gusta_baja(catalogo):
    votos = {"Prote0": config.VOTO_ME_GUSTA, "Carbo0": config.VOTO_NO_ME_GUSTA}
    puntajes = preferencias.calcular_preferencias(catalogo, votos)
    assert puntajes["Prote0"] > config.PREFERENCIA_NEUTRA
    assert puntajes["Carbo0"] < config.PREFERENCIA_NEUTRA


def test_los_puntajes_estan_entre_0_y_1(catalogo):
    votos = {f"Prote{i}": config.VOTO_ME_GUSTA for i in range(8)}
    votos |= {f"Carbo{i}": config.VOTO_NO_ME_GUSTA for i in range(8)}
    for puntaje in preferencias.calcular_preferencias(catalogo, votos).values():
        assert 0.0 <= puntaje <= 1.0


def test_lo_parecido_sube_mas_que_lo_distinto(catalogo):
    """Si te gusta Prote3, Prote4 (casi igual) sube más que una fruta."""
    puntajes = preferencias.calcular_preferencias(catalogo, {"Prote3": config.VOTO_ME_GUSTA})
    assert puntajes["Prote4"] > puntajes["Fruta4"]


def test_mas_votos_coherentes_dan_mas_confianza(catalogo):
    uno = preferencias.calcular_preferencias(catalogo, {"Prote3": config.VOTO_ME_GUSTA})
    tres = preferencias.calcular_preferencias(
        catalogo, {n: config.VOTO_ME_GUSTA for n in ("Prote2", "Prote3", "Prote5")}
    )
    assert tres["Prote4"] > uno["Prote4"]


def test_un_voto_no_bloquea_alimentos_no_se_excluye_nada(catalogo):
    """"No me gusta" es suave: baja el puntaje pero nunca lo deja en 0 con un solo voto."""
    puntajes = preferencias.calcular_preferencias(catalogo, {"Prote0": config.VOTO_NO_ME_GUSTA})
    assert puntajes["Prote0"] > 0.0


def test_votos_de_alimentos_que_ya_no_existen_se_ignoran(catalogo):
    assert preferencias.calcular_preferencias(catalogo, {"Fantasma": config.VOTO_ME_GUSTA}) == {}


def test_datos_faltantes_no_rompen_los_vectores(catalogo):
    catalogo[0]["iron_mg"] = None
    catalogo[1]["price_per_kg_ref"] = None
    vectores = preferencias.construir_vectores(catalogo)
    assert len(vectores) == len(catalogo)
    assert all(isinstance(x, float) for v in vectores.values() for x in v)
    # y el dato del catálogo NO se modifica (sigue siendo "sin dato")
    assert catalogo[0]["iron_mg"] is None


def test_vectores_centrados(catalogo):
    vectores = list(preferencias.construir_vectores(catalogo).values())
    for k in range(len(vectores[0])):
        assert abs(sum(v[k] for v in vectores) / len(vectores)) < 1e-9


def test_vectores_de_catalogo_vacio():
    assert preferencias.construir_vectores([]) == {}


def test_similitud_coseno_casos_basicos():
    assert preferencias.similitud_coseno([1, 0], [1, 0]) == pytest.approx(1.0)
    assert preferencias.similitud_coseno([1, 0], [-1, 0]) == pytest.approx(-1.0)
    assert preferencias.similitud_coseno([1, 0], [0, 1]) == pytest.approx(0.0)
    assert preferencias.similitud_coseno([0, 0], [1, 1]) == 0.0


def test_resolver_alimento(catalogo):
    assert preferencias.resolver_alimento(catalogo, "  prote0 ") == "Prote0"
    for malo in ("NoExiste", "", "   ", None, 123):
        with pytest.raises(ErrorValidacion):
            preferencias.resolver_alimento(catalogo, malo)


def test_resumen_solo_incluye_alimentos_usables(catalogo):
    catalogo.append(_alimento("Aceite", "otro", 884, 0, 0, 100, 0, 0, 9))
    puntajes = {a["name"]: 0.5 for a in catalogo}
    puntajes["Aceite"] = 0.99
    resumen = preferencias.resumir_preferencias(catalogo, puntajes, 3)
    nombres = [x["nombre"] for x in resumen["mas_recomendados"] + resumen["menos_recomendados"]]
    assert "Aceite" not in nombres
    assert len(resumen["mas_recomendados"]) == 3


def test_el_menu_incorpora_mas_lo_que_le_gusta(catalogo):
    """Integración con el recomendador: los alimentos votados con "me gusta" se usan más."""
    favoritos = [f"Prote{i}" for i in (6, 7)] + [f"Carbo{i}" for i in (6, 7)]
    sin = recomendador.generar_menu(catalogo, 400, 2)
    votos = {n: config.VOTO_ME_GUSTA for n in favoritos}
    con = recomendador.generar_menu(
        catalogo, 400, 2, preferencias=preferencias.calcular_preferencias(catalogo, votos)
    )

    def usos(menu):
        return sum(1 for c in menu["comidas"] for i in c["ingredientes"] if i["nombre"] in favoritos)

    assert usos(con) >= usos(sin)
    assert con["costo_total"] <= 400


# --- Validadores nuevos de app.validacion ---------------------------------
@pytest.mark.parametrize("valido", ["familia_perez", "u1", "Ana-2.0", "a" * config.USUARIO_ID_MAX_LARGO])
def test_usuario_id_valido(valido):
    assert validar_usuario_id(valido) == valido


@pytest.mark.parametrize("malo", ["", "   ", "a b", "x;DROP TABLE", "ñandú", "a" * 51, None, 5, "a\nb"])
def test_usuario_id_invalido(malo):
    with pytest.raises(ErrorValidacion):
        validar_usuario_id(malo)


def test_voto_valido_e_invalido():
    assert validar_voto(" Me_Gusta ") == "me_gusta"
    assert validar_voto("no_me_gusta") == "no_me_gusta"
    for malo in ("quizas", "", None, 1, True):
        with pytest.raises(ErrorValidacion):
            validar_voto(malo)
