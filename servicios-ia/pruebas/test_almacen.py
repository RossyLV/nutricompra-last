"""Pruebas del almacén de votos en SQLite (Fase 4)."""
import pytest

from app.almacen import Almacen


@pytest.fixture
def almacen(tmp_path):
    """Un almacén con su propia base de datos temporal (no toca la real)."""
    return Almacen(tmp_path / "prueba.db")


def test_crear_el_almacen_no_crea_el_archivo(tmp_path):
    ruta = tmp_path / "carpeta" / "nueva.db"
    Almacen(ruta)
    assert not ruta.exists()


def test_se_crea_el_archivo_al_primer_uso(tmp_path):
    ruta = tmp_path / "carpeta" / "nueva.db"
    Almacen(ruta).registrar_voto("ana", "Quinua", "me_gusta")
    assert ruta.exists()


def test_usuario_nuevo_no_tiene_votos(almacen):
    assert almacen.obtener_votos("nadie") == {}
    assert almacen.obtener_historial("nadie") == []


def test_registrar_y_leer_votos(almacen):
    assert almacen.registrar_voto("ana", "Quinua", "me_gusta") == 1
    assert almacen.registrar_voto("ana", "Hígado", "no_me_gusta") == 2
    assert almacen.obtener_votos("ana") == {"Hígado": "no_me_gusta", "Quinua": "me_gusta"}


def test_el_ultimo_voto_reemplaza_al_anterior(almacen):
    almacen.registrar_voto("ana", "Quinua", "me_gusta")
    total = almacen.registrar_voto("ana", "Quinua", "no_me_gusta")
    assert total == 1  # sigue siendo un solo alimento votado
    assert almacen.obtener_votos("ana") == {"Quinua": "no_me_gusta"}


def test_el_historial_guarda_todos_los_votos_en_orden(almacen):
    almacen.registrar_voto("ana", "Quinua", "me_gusta")
    almacen.registrar_voto("ana", "Papa", "me_gusta")
    almacen.registrar_voto("ana", "Quinua", "no_me_gusta")
    historial = almacen.obtener_historial("ana")
    assert [h["numero"] for h in historial] == [1, 2, 3]
    assert [h["alimento"] for h in historial] == ["Quinua", "Papa", "Quinua"]
    assert historial[2]["voto"] == "no_me_gusta"


def test_los_usuarios_estan_aislados(almacen):
    almacen.registrar_voto("ana", "Quinua", "me_gusta")
    almacen.registrar_voto("luis", "Quinua", "no_me_gusta")
    assert almacen.obtener_votos("ana") == {"Quinua": "me_gusta"}
    assert almacen.obtener_votos("luis") == {"Quinua": "no_me_gusta"}


def test_reiniciar_borra_solo_a_ese_usuario(almacen):
    almacen.registrar_voto("ana", "Quinua", "me_gusta")
    almacen.registrar_voto("ana", "Papa", "me_gusta")
    almacen.registrar_voto("luis", "Quinua", "me_gusta")
    assert almacen.reiniciar("ana") == 2
    assert almacen.obtener_votos("ana") == {}
    assert almacen.obtener_historial("ana") == []
    assert almacen.obtener_votos("luis") == {"Quinua": "me_gusta"}


def test_los_textos_raros_se_guardan_como_datos_no_como_sql(almacen):
    """Un nombre con comillas no rompe la base ni ejecuta nada (consultas con parámetros)."""
    raro = "'; DROP TABLE votos; --"
    almacen.registrar_voto("ana", raro, "me_gusta")
    assert almacen.obtener_votos("ana") == {raro: "me_gusta"}
    assert almacen.obtener_votos("otra") == {}  # la tabla sigue existiendo


def test_la_base_rechaza_un_voto_invalido(almacen):
    import sqlite3
    with pytest.raises(sqlite3.IntegrityError):
        almacen.registrar_voto("ana", "Quinua", "quizas")
