"""Demostración: el menú se acerca a los gustos del usuario a medida que vota.

Cómo funciona la simulación (todo con datos de ejemplo, sin personas reales):
1. Se define un "gusto oculto" que el sistema NO conoce (por ejemplo, "le gustan
   los alimentos calóricos"). Esto hace de usuario ficticio.
2. El usuario ficticio vota alimentos al azar según ese gusto (me gusta / no me gusta).
3. Con 0, 5, 10 y 20 votos se genera el menú y se mide qué porcentaje de sus
   ingredientes le gustan al usuario.
4. Con 0 votos es el menú SIN personalización (la línea base). Se repite varias
   veces con votos distintos para promediar y no depender de la suerte.

También se muestra el balance nutricional y el costo, para comprobar que
personalizar no estropea la nutrición ni el presupuesto.

Uso (desde la carpeta servicios-ia, con el entorno virtual activo):
    python evaluacion/demo_preferencias.py
    python evaluacion/demo_preferencias.py --presupuesto 140 --personas 4 --repeticiones 8
"""
import argparse
import random
import sys
from pathlib import Path
from statistics import median

# Permite importar "app" aunque el script se ejecute desde otra carpeta.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))

from app import catalogo as cat  # noqa: E402
from app import config, preferencias, recomendador  # noqa: E402

CANTIDADES_DE_VOTOS = (0, 5, 10, 20)


def alimentos_votables(catalogo: list[dict]) -> list[dict]:
    """Alimentos que el recomendador puede usar (los que tiene sentido votar)."""
    return [
        a for a in catalogo
        if a["app_category"] in config.CATEGORIAS_APP
        and a["name"] not in config.INGREDIENTES_EXCLUIDOS
        and a["price_per_kg_ref"] is not None
    ]


def gusto_oculto(catalogo: list[dict], nutriente: str, le_gusta_alto: bool) -> set[str]:
    """Conjunto de alimentos que le gustan al usuario ficticio.

    Regla: dentro de cada categoría, le gustan los que están por encima de la
    mediana en ese nutriente (si le_gusta_alto) o por debajo (si no).
    """
    gustan: set[str] = set()
    for categoria in config.CATEGORIAS_APP:
        grupo = [a for a in alimentos_votables(catalogo)
                 if a["app_category"] == categoria and a[nutriente] is not None]
        if not grupo:
            continue
        corte = median(a[nutriente] for a in grupo)
        for a in grupo:
            if (a[nutriente] > corte) == le_gusta_alto:
                gustan.add(a["name"])
    return gustan


def porcentaje_que_gusta(menu: dict, gustan: set[str]) -> float:
    """% de los ingredientes del menú (63 en total) que le gustan al usuario."""
    nombres = [i["nombre"] for comida in menu["comidas"] for i in comida["ingredientes"]]
    return 100 * sum(1 for n in nombres if n in gustan) / len(nombres)


def simular(catalogo, gustan, presupuesto, personas, repeticiones, semilla) -> list[dict]:
    """Para cada cantidad de votos, promedia los resultados de varias repeticiones."""
    votables = [a["name"] for a in alimentos_votables(catalogo)]
    filas = []
    for cantidad in CANTIDADES_DE_VOTOS:
        gusto, balance, costo = [], [], []
        for rep in range(1 if cantidad == 0 else repeticiones):
            azar = random.Random(semilla + rep)
            elegidos = azar.sample(votables, cantidad)
            votos = {n: (config.VOTO_ME_GUSTA if n in gustan else config.VOTO_NO_ME_GUSTA)
                     for n in elegidos}
            prefs = preferencias.calcular_preferencias(catalogo, votos)
            menu = recomendador.generar_menu(catalogo, presupuesto, personas, preferencias=prefs)
            gusto.append(porcentaje_que_gusta(menu, gustan))
            balance.append(menu["puntaje_balance"])
            costo.append(menu["costo_total"])
        n = len(gusto)
        filas.append({
            "votos": cantidad,
            "gusta": sum(gusto) / n,
            "balance": sum(balance) / n,
            "costo": sum(costo) / n,
        })
    return filas


def mostrar(titulo: str, filas: list[dict]) -> None:
    base = filas[0]["gusta"]
    print(f"\n{titulo}")
    print(f"  {'votos':>5} | {'ingredientes que le gustan':>27} | {'balance':>8} | {'costo (S/)':>10}")
    print("  " + "-" * 62)
    for f in filas:
        cambio = "" if f["votos"] == 0 else f"  ({f['gusta'] - base:+.1f} puntos)"
        print(f"  {f['votos']:>5} | {f['gusta']:>26.1f}% | {f['balance']:>7.1f}% | {f['costo']:>10.2f}{cambio}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Demostración de preferencias (Fase 4).")
    parser.add_argument("--presupuesto", type=float, default=140, help="Soles por semana (default 140)")
    parser.add_argument("--personas", type=int, default=4, help="Personas del hogar (default 4)")
    parser.add_argument("--repeticiones", type=int, default=6, help="Repeticiones por cantidad de votos")
    parser.add_argument("--semilla", type=int, default=100, help="Semilla del azar (resultados repetibles)")
    parser.add_argument("--peso", type=float, default=None,
                        help="Prueba otro PESO_PREFERENCIA sin tocar config.py")
    args = parser.parse_args()
    if args.peso is not None:
        config.PESO_PREFERENCIA = args.peso

    catalogo = cat.cargar_catalogo()
    print(f"Catálogo: {len(catalogo)} alimentos | presupuesto S/ {args.presupuesto:g} "
          f"para {args.personas} personas | PESO_PREFERENCIA = {config.PESO_PREFERENCIA}")
    perfiles = [
        ("Perfil A: le gustan los alimentos calóricos", "energy_kcal", True),
        ("Perfil B: le gustan los alimentos ligeros (pocas calorías)", "energy_kcal", False),
        ("Perfil C: le gustan los alimentos ricos en proteína", "protein_g", True),
    ]
    for titulo, nutriente, alto in perfiles:
        gustan = gusto_oculto(catalogo, nutriente, alto)
        filas = simular(catalogo, gustan, args.presupuesto, args.personas, args.repeticiones, args.semilla)
        mostrar(titulo, filas)
    print("\nLectura: con 0 votos es el menú sin personalización (línea base). Si la columna "
          "'ingredientes que le gustan' sube con los votos, el sistema está aprendiendo.")


if __name__ == "__main__":
    main()
