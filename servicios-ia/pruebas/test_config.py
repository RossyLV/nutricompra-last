"""Pruebas de la configuración base (Fase 0)."""
from app import config


def test_total_comidas_semana_es_21():
    # 7 días x 3 comidas al día
    assert config.TOTAL_COMIDAS_SEMANA == 21


def test_categorias_app_son_cinco():
    assert len(config.CATEGORIAS_APP) == 5


def test_tamano_maximo_imagen_es_positivo():
    assert config.TAMANO_MAX_IMAGEN_MB > 0
