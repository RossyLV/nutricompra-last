"""Recomendador de menú semanal (21 comidas).

Objetivo: armar el menú con MEJOR balance nutricional sin pasarse del presupuesto,
inclinándose por los alimentos que le gustan al usuario (si hay preferencias).

Cómo funciona, en simple:
1. Se arma un menú inicial con los ingredientes más baratos. Si ni así alcanza
   el presupuesto, se avisa cuánto haría falta.
2. Se mejora por intercambios: se cambia un ingrediente al azar por otro de la
   misma categoría y se queda el cambio solo si el menú mejora, cumple las
   reglas y no se pasa del presupuesto. Se repite miles de veces.
"""
import random
from collections import Counter

from app import config
from app.nutricion import aporte_porcion, porcion_g, puntaje_dia, puntaje_nutriente, sumar_aportes
from app.validacion import ErrorValidacion, validar_personas, validar_presupuesto

DIAS = range(1, config.DIAS_SEMANA + 1)


class ErrorPresupuestoInsuficiente(ErrorValidacion):
    """El presupuesto no alcanza ni para el menú más barato posible."""

    def __init__(self, costo_minimo: float):
        self.costo_minimo = costo_minimo
        super().__init__(
            f"El presupuesto no alcanza para un menú de {config.TOTAL_COMIDAS_SEMANA} comidas. "
            f"Necesitas al menos S/ {costo_minimo:.2f} (estimado con los precios actuales)."
        )


# ---------------------------------------------------------------------------
# Preparación de datos
# ---------------------------------------------------------------------------
def _preparar_ingredientes(catalogo: list[dict]) -> dict[str, dict]:
    """Deja por cada ingrediente utilizable: categoría, costo por persona y aportes.

    Se descartan los de categoría "otro" (aceites, azúcar...), los ingredientes
    excluidos (condimentos, harina) y los que no tienen precio.
    """
    datos: dict[str, dict] = {}
    for alimento in catalogo:
        categoria = alimento["app_category"]
        if (
            categoria not in config.CATEGORIAS_APP
            or alimento["price_per_kg_ref"] is None
            or alimento["name"] in config.INGREDIENTES_EXCLUIDOS
        ):
            continue
        gramos = porcion_g(alimento)
        datos[alimento["name"]] = {
            "categoria": categoria,
            "porcion_g": gramos,
            "precio_kg": alimento["price_per_kg_ref"],
            "costo_pp": alimento["price_per_kg_ref"] * gramos / 1000,  # S/ por persona
            "aporte": aporte_porcion(alimento),
        }
    return datos


def _candidatos_por_categoria(datos: dict[str, dict]) -> dict[str, list[str]]:
    """Agrupa los ingredientes por categoría, del más barato al más caro."""
    grupos: dict[str, list[str]] = {c: [] for c in config.CATEGORIAS_APP}
    for nombre, d in datos.items():
        grupos[d["categoria"]].append(nombre)
    for lista in grupos.values():
        lista.sort(key=lambda n: datos[n]["costo_pp"])
    return grupos


def _lista_de_comidas() -> list[tuple[int, str]]:
    """Las 21 comidas de la semana como (día, momento): (1,'desayuno'), (1,'almuerzo')..."""
    return [(dia, momento) for dia in DIAS for momento in config.MOMENTOS_DEL_DIA]


# ---------------------------------------------------------------------------
# Reglas y puntajes del menú
# ---------------------------------------------------------------------------
# Un menú es una lista de 21 diccionarios {categoria: ingrediente}, en el orden de _lista_de_comidas().
def _cumple_reglas(menu: list[dict], comidas: list[tuple[int, str]]) -> bool:
    """Reglas de variedad: máximo de repeticiones y proteína distinta en almuerzo y cena."""
    conteo = Counter(nombre for comida in menu for nombre in comida.values())
    if max(conteo.values()) > config.MAX_REPETICIONES_SEMANA:
        return False
    for i, (_, momento) in enumerate(comidas):
        if momento == "cena" and menu[i]["proteina"] == menu[i - 1]["proteina"]:
            return False
    return True


def _costo_por_persona(menu: list[dict], datos: dict[str, dict]) -> float:
    return sum(datos[n]["costo_pp"] for comida in menu for n in comida.values())


def _totales_por_dia(menu: list[dict], datos: dict[str, dict]) -> list[dict[str, float]]:
    """Nutrientes de cada día (por persona), sumando sus 3 comidas."""
    por_dia = []
    por_comida = len(config.MOMENTOS_DEL_DIA)
    for d in range(config.DIAS_SEMANA):
        aportes = [
            datos[n]["aporte"]
            for comida in menu[d * por_comida:(d + 1) * por_comida]
            for n in comida.values()
        ]
        totales, _ = sumar_aportes(aportes)
        por_dia.append(totales)
    return por_dia


def _puntaje_balance(menu: list[dict], datos: dict[str, dict]) -> float:
    """Puntaje de balance de la semana (0 a 1): promedio del puntaje de cada día."""
    dias = _totales_por_dia(menu, datos)
    return sum(puntaje_dia(t) for t in dias) / len(dias)


def _objetivo(menu, datos, presupuesto_pp, preferencias) -> float:
    """Función que se quiere maximizar: balance + variedad + preferencias - costo."""
    nombres = [n for comida in menu for n in comida.values()]
    balance = _puntaje_balance(menu, datos)
    variedad = len(set(nombres)) / len(nombres)
    gusto = sum(preferencias.get(n, config.PREFERENCIA_NEUTRA) for n in nombres) / len(nombres)
    costo_relativo = _costo_por_persona(menu, datos) / presupuesto_pp
    return (
        balance
        + config.PESO_VARIEDAD * variedad
        + config.PESO_PREFERENCIA * gusto
        - config.PESO_COSTO * costo_relativo
    )


# ---------------------------------------------------------------------------
# Construcción del menú
# ---------------------------------------------------------------------------
def _menu_inicial_barato(comidas, grupos) -> list[dict]:
    """Menú de partida: en cada hueco, el ingrediente más barato que cumpla las reglas."""
    uso: Counter = Counter()
    menu: list[dict] = []
    for i, (_, momento) in enumerate(comidas):
        comida: dict[str, str] = {}
        for categoria in config.ESTRUCTURA_COMIDAS[momento]:
            for nombre in grupos[categoria]:  # ya vienen ordenados de barato a caro
                repite_proteina = (
                    momento == "cena" and categoria == "proteina"
                    and nombre == menu[i - 1]["proteina"]
                )
                if uso[nombre] < config.MAX_REPETICIONES_SEMANA and not repite_proteina:
                    comida[categoria] = nombre
                    uso[nombre] += 1
                    break
        menu.append(comida)
    return menu


def _mejorar_menu(menu, comidas, grupos, datos, presupuesto, personas, preferencias, iteraciones, rng):
    """Mejora el menú por intercambios aleatorios (solo se aceptan mejoras válidas)."""
    presupuesto_pp = presupuesto / personas
    actual = _objetivo(menu, datos, presupuesto_pp, preferencias)
    for _ in range(iteraciones):
        posicion = rng.randrange(len(menu))
        categoria = rng.choice(list(menu[posicion]))
        nuevo = rng.choice(grupos[categoria])
        anterior = menu[posicion][categoria]
        if nuevo == anterior:
            continue
        menu[posicion][categoria] = nuevo
        if _cumple_reglas(menu, comidas) and _costo_por_persona(menu, datos) <= presupuesto_pp:
            puntaje = _objetivo(menu, datos, presupuesto_pp, preferencias)
            if puntaje > actual + 1e-12:
                actual = puntaje
                continue
        menu[posicion][categoria] = anterior  # no sirvió: se deshace el cambio
    return menu


def generar_menu(
    catalogo: list[dict],
    presupuesto,
    personas,
    preferencias: dict[str, float] | None = None,
    semilla: int = config.SEMILLA_POR_DEFECTO,
    iteraciones: int = config.ITERACIONES_BUSQUEDA,
) -> dict:
    """Genera el menú semanal de 21 comidas.

    - presupuesto: soles disponibles para la semana (> 0).
    - personas: integrantes del hogar (>= 1).
    - preferencias: {nombre_alimento: puntaje de 0 a 1}; 0.5 es neutral.
    Lanza ErrorValidacion o ErrorPresupuestoInsuficiente.
    """
    presupuesto = validar_presupuesto(presupuesto)
    personas = validar_personas(personas)
    preferencias = preferencias or {}

    datos = _preparar_ingredientes(catalogo)
    grupos = _candidatos_por_categoria(datos)
    comidas = _lista_de_comidas()

    menu = _menu_inicial_barato(comidas, grupos)
    costo_minimo = _costo_por_persona(menu, datos) * personas
    if costo_minimo > presupuesto:
        raise ErrorPresupuestoInsuficiente(costo_minimo)

    puntaje_inicial = _puntaje_balance(menu, datos)
    menu = _mejorar_menu(
        menu, comidas, grupos, datos, presupuesto, personas,
        preferencias, iteraciones, random.Random(semilla),
    )
    return _armar_respuesta(menu, comidas, datos, presupuesto, personas, puntaje_inicial)


# ---------------------------------------------------------------------------
# Respuesta
# ---------------------------------------------------------------------------
def _armar_respuesta(menu, comidas, datos, presupuesto, personas, puntaje_inicial) -> dict:
    """Convierte el menú en un resultado claro: comidas, balance y lista de compras."""
    detalle_comidas = []
    for (dia, momento), comida in zip(comidas, menu):
        ingredientes = []
        for categoria, nombre in comida.items():
            gramos = datos[nombre]["porcion_g"]
            ingredientes.append({
                "nombre": nombre,
                "categoria": categoria,
                "gramos_por_persona": gramos,
                "costo": round(datos[nombre]["costo_pp"] * personas, 2),
            })
        detalle_comidas.append({
            "dia": dia,
            "momento": momento,
            "ingredientes": ingredientes,
            "costo": round(sum(i["costo"] for i in ingredientes), 2),
        })

    costo_total = _costo_por_persona(menu, datos) * personas
    dias = _totales_por_dia(menu, datos)
    promedio = {n: sum(d[n] for d in dias) / len(dias) for n in config.NUTRIENTES_BALANCE}
    balance = {}
    for nutriente, regla in config.REQUERIMIENTOS.items():
        balance[nutriente] = {
            "nombre": regla["nombre"],
            "promedio_diario_por_persona": round(promedio[nutriente], 1),
            "minimo": regla["min"],
            "maximo": regla.get("max"),
            "puntaje": round(puntaje_nutriente(promedio[nutriente], regla) * 100, 1),
        }

    # Lista de compras: se suman los gramos de cada ingrediente para todo el hogar
    gramos_totales: Counter = Counter()
    for comida in menu:
        for categoria, nombre in comida.items():
            gramos_totales[nombre] += datos[nombre]["porcion_g"] * personas
    lista_compras = [
        {
            "nombre": nombre,
            "categoria": datos[nombre]["categoria"],
            "gramos": gramos,
            "costo": round(gramos / 1000 * datos[nombre]["precio_kg"], 2),
        }
        for nombre, gramos in sorted(gramos_totales.items(), key=lambda x: (datos[x[0]]["categoria"], x[0]))
    ]

    # Aviso de datos nutricionales faltantes (para no presentar cifras como exactas)
    incompletos = sorted({
        nombre for comida in menu for nombre in comida.values()
        if any(v is None for v in datos[nombre]["aporte"].values())
    })
    avisos = []
    if incompletos:
        avisos.append(
            "Faltan datos nutricionales de: " + ", ".join(incompletos)
            + ". Los totales de esos nutrientes pueden estar subestimados."
        )

    return {
        "presupuesto": round(presupuesto, 2),
        "personas": personas,
        "costo_total": round(costo_total, 2),
        "ahorro": round(presupuesto - costo_total, 2),
        "puntaje_balance": round(_puntaje_balance(menu, datos) * 100, 1),
        "puntaje_balance_menu_basico": round(puntaje_inicial * 100, 1),
        "comidas": detalle_comidas,
        "balance": balance,
        "lista_compras": lista_compras,
        "avisos": avisos,
    }
