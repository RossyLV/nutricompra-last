"""Pruebas de la validación de entradas (Fase 1)."""
import pytest

from app.validacion import (
    ErrorValidacion,
    validar_categoria,
    validar_imagen,
    validar_personas,
    validar_presupuesto,
)


# ---------- Presupuesto ----------
@pytest.mark.parametrize("valor, esperado", [(150, 150.0), (99.5, 99.5), ("200", 200.0)])
def test_presupuesto_valido(valor, esperado):
    assert validar_presupuesto(valor) == esperado


@pytest.mark.parametrize(
    "valor", [0, -10, "abc", None, True, float("nan"), float("inf"), 1_000_000]
)
def test_presupuesto_invalido(valor):
    with pytest.raises(ErrorValidacion):
        validar_presupuesto(valor)


# ---------- Personas ----------
@pytest.mark.parametrize("valor, esperado", [(1, 1), (4, 4), ("3", 3), (2.0, 2)])
def test_personas_valido(valor, esperado):
    assert validar_personas(valor) == esperado


@pytest.mark.parametrize("valor", [0, -1, 2.5, "dos", None, True, 21])
def test_personas_invalido(valor):
    with pytest.raises(ErrorValidacion):
        validar_personas(valor)


# ---------- Categoría ----------
def test_categoria_valida_ignora_mayusculas_y_espacios():
    assert validar_categoria("  Proteina ") == "proteina"


@pytest.mark.parametrize("valor", ["postre", "", 5, None])
def test_categoria_invalida(valor):
    with pytest.raises(ErrorValidacion):
        validar_categoria(valor)


# ---------- Imagen ----------
def test_imagen_valida():
    validar_imagen("image/jpeg", 1024)  # no debe lanzar error


def test_imagen_formato_no_permitido():
    with pytest.raises(ErrorValidacion):
        validar_imagen("application/pdf", 1024)


def test_imagen_vacia():
    with pytest.raises(ErrorValidacion):
        validar_imagen("image/png", 0)


def test_imagen_demasiado_grande():
    seis_megas = 6 * 1024 * 1024  # el máximo por defecto es 5 MB
    with pytest.raises(ErrorValidacion):
        validar_imagen("image/png", seis_megas)
