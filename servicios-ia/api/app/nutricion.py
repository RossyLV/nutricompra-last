"""Cálculos nutricionales: aporte de una porción y puntaje de balance.

Regla importante: un dato nutricional vacío (None) significa "la fuente no lo
trae". NUNCA se convierte en 0: se omite de la suma y se reporta como faltante.
"""
from app import config


def porcion_g(alimento: dict) -> int:
    """Gramos de una porción por persona: excepción por nombre, luego por TPCA, luego por categoría."""
    nombre = alimento["name"]
    if nombre in config.PORCIONES_ESPECIALES_POR_NOMBRE_G:
        return config.PORCIONES_ESPECIALES_POR_NOMBRE_G[nombre]
    if alimento["category"] in config.PORCIONES_ESPECIALES_POR_TPCA_G:
        return config.PORCIONES_ESPECIALES_POR_TPCA_G[alimento["category"]]
    return config.PORCIONES_G[alimento["app_category"]]


def aporte_porcion(alimento: dict) -> dict[str, float | None]:
    """Nutrientes que aporta UNA porción (por persona) de un alimento.

    El catálogo trae los valores por 100 g; se escalan al tamaño de su porción.
    Si el nutriente falta, queda en None.
    """
    gramos = porcion_g(alimento)
    referencia = alimento.get("reference_amount") or 100.0
    factor = gramos / referencia
    return {
        nutriente: (None if alimento[nutriente] is None else alimento[nutriente] * factor)
        for nutriente in config.NUTRIENTES_BALANCE
    }


def sumar_aportes(aportes: list[dict[str, float | None]]) -> tuple[dict[str, float], dict[str, int]]:
    """Suma los aportes de varios alimentos.

    Devuelve (totales, faltantes): los datos vacíos no suman y se cuentan aparte.
    """
    totales = {n: 0.0 for n in config.NUTRIENTES_BALANCE}
    faltantes = {n: 0 for n in config.NUTRIENTES_BALANCE}
    for aporte in aportes:
        for nutriente, valor in aporte.items():
            if valor is None:
                faltantes[nutriente] += 1
            else:
                totales[nutriente] += valor
    return totales, faltantes


def puntaje_nutriente(valor: float, regla: dict) -> float:
    """Puntaje de 0 a 1 de un nutriente frente a su requerimiento.

    - "minimo": llegar o superar el mínimo da 1; si falta, es la fracción alcanzada.
    - "rango": 1 dentro del rango; fuera del rango baja proporcionalmente.
    """
    minimo = regla["min"]
    if regla["tipo"] == "minimo":
        return min(valor / minimo, 1.0)
    maximo = regla["max"]
    if valor < minimo:
        return valor / minimo
    if valor > maximo:
        return max(0.0, 1.0 - (valor - maximo) / maximo)
    return 1.0


def puntaje_dia(totales_dia: dict[str, float]) -> float:
    """Puntaje de 0 a 1 de un día: promedio del puntaje de cada nutriente."""
    puntajes = [
        puntaje_nutriente(totales_dia[n], config.REQUERIMIENTOS[n])
        for n in config.NUTRIENTES_BALANCE
    ]
    return sum(puntajes) / len(puntajes)
