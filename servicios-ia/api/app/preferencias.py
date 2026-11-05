"""Preferencias del usuario: aprender de los "me gusta / no me gusta".

Técnica: FILTRADO BASADO EN CONTENIDO. Idea en simple:

1. Cada alimento se "describe" con una lista de números (su vector): a qué
   categoría pertenece, cuántos nutrientes tiene y qué tan caro es.
2. Dos alimentos se parecen cuando sus vectores apuntan en la misma dirección
   (similitud del coseno: 1 = muy parecidos, 0 = nada que ver, -1 = opuestos).
3. Si al usuario le gustó la lenteja, también sube el puntaje de los alimentos
   que se parecen a la lenteja (aunque nunca los haya votado). Si le disgustó
   algo, baja el puntaje de lo parecido.
4. El resultado es un puntaje de 0 a 1 por alimento (0.5 = neutro), que es
   justo lo que espera `recomendador.generar_menu(preferencias=...)`.

Todo está hecho con Python simple (listas y math), sin librerías extra.
"""
import math
from statistics import median

from app import config
from app.catalogo import buscar_alimento
from app.validacion import ErrorValidacion


# ---------------------------------------------------------------------------
# Validación del alimento votado
# ---------------------------------------------------------------------------
def resolver_alimento(catalogo: list[dict], nombre) -> str:
    """Comprueba que el alimento exista en el catálogo y devuelve su nombre oficial.

    Acepta cualquier combinación de mayúsculas ("quinua" -> "Quinua").
    Lanza ErrorValidacion si no es un texto o si no existe.
    """
    if not isinstance(nombre, str) or not nombre.strip():
        raise ErrorValidacion("Debes indicar el nombre de un alimento.")
    alimento = buscar_alimento(catalogo, nombre)
    if alimento is None:
        raise ErrorValidacion(f"No existe el alimento '{nombre.strip()}' en el catálogo.")
    return alimento["name"]


# ---------------------------------------------------------------------------
# Paso 1: describir cada alimento con un vector
# ---------------------------------------------------------------------------
def _columna_normalizada(catalogo: list[dict], columna: str) -> list[float]:
    """Valores de una columna del catálogo, llevados a la escala 0 a 1 (por posición).

    Si un alimento no tiene el dato (None), SOLO PARA MEDIR PARECIDO se usa la
    mediana de su categoría. Esto no cambia el balance nutricional: allí el
    dato faltante sigue siendo "sin dato", nunca 0.
    """
    por_categoria: dict[str, list[float]] = {}
    for alimento in catalogo:
        if alimento[columna] is not None:
            por_categoria.setdefault(alimento["app_category"], []).append(alimento[columna])
    todos = [v for valores in por_categoria.values() for v in valores]
    mediana_global = median(todos) if todos else 0.0

    valores: list[float] = []
    for alimento in catalogo:
        valor = alimento[columna]
        if valor is None:
            de_su_categoria = por_categoria.get(alimento["app_category"])
            valor = median(de_su_categoria) if de_su_categoria else mediana_global
        valores.append(float(valor))

    return _posicion_relativa(valores)


def _posicion_relativa(valores: list[float]) -> list[float]:
    """Lleva cada valor a su POSICIÓN entre todos, de 0 (el menor) a 1 (el mayor).

    Se usa la posición y no el valor directo para que un caso extremo (por ejemplo
    el aceite, con 884 kcal) no aplaste a todos los demás. Si hay empates, comparten
    la posición intermedia.
    """
    cantidad = len(valores)
    if cantidad < 2 or max(valores) == min(valores):  # todos iguales: no distingue nada
        return [0.0] * cantidad
    posiciones = []
    for valor in valores:
        menores = sum(1 for otro in valores if otro < valor)
        iguales = sum(1 for otro in valores if otro == valor)
        posiciones.append((menores + (iguales - 1) / 2) / (cantidad - 1))
    return posiciones


def construir_vectores(catalogo: list[dict]) -> dict[str, list[float]]:
    """Devuelve {nombre_del_alimento: vector} para todo el catálogo.

    El vector tiene tres grupos de características:
    - categoría de la app (vegetal, proteína...), en forma "una sola activa";
    - nutrientes por 100 g, normalizados entre 0 y 1;
    - precio por kg, normalizado entre 0 y 1.
    Cada grupo se escala según config.PESOS_CARACTERISTICAS. Al final se resta el
    promedio del catálogo ("centrar"), para que "parecido" signifique "más
    parecido de lo normal" y no "todo se parece un poco a todo".
    """
    if not catalogo:
        return {}
    pesos = config.PESOS_CARACTERISTICAS
    categorias = config.CATEGORIAS_CATALOGO
    nutrientes = [_columna_normalizada(catalogo, c) for c in config.NUTRIENTES_CONTENIDO]
    precios = _columna_normalizada(catalogo, "price_per_kg_ref")

    escala_categoria = math.sqrt(pesos["categoria"])
    escala_nutriente = math.sqrt(pesos["nutrientes"] / len(nutrientes))
    escala_precio = math.sqrt(pesos["precio"])

    vectores: list[list[float]] = []
    for i, alimento in enumerate(catalogo):
        vector = [escala_categoria * (1.0 if alimento["app_category"] == c else 0.0) for c in categorias]
        vector += [escala_nutriente * columna[i] for columna in nutrientes]
        vector.append(escala_precio * precios[i])
        vectores.append(vector)

    dimension = len(vectores[0])
    promedio = [sum(v[k] for v in vectores) / len(vectores) for k in range(dimension)]
    return {
        alimento["name"]: [x - m for x, m in zip(vector, promedio)]
        for alimento, vector in zip(catalogo, vectores)
    }


# ---------------------------------------------------------------------------
# Paso 2: medir el parecido
# ---------------------------------------------------------------------------
def similitud_coseno(a: list[float], b: list[float]) -> float:
    """Parecido entre dos vectores: 1 = misma dirección, 0 = sin relación, -1 = opuestos."""
    producto = sum(x * y for x, y in zip(a, b))
    norma_a = math.sqrt(sum(x * x for x in a))
    norma_b = math.sqrt(sum(y * y for y in b))
    if norma_a == 0 or norma_b == 0:  # un vector vacío no se parece a nada
        return 0.0
    return producto / (norma_a * norma_b)


# ---------------------------------------------------------------------------
# Paso 3: convertir los votos en un puntaje por alimento
# ---------------------------------------------------------------------------
def calcular_preferencias(catalogo: list[dict], votos: dict[str, str]) -> dict[str, float]:
    """Puntaje de preferencia (0 a 1) de cada alimento a partir de los votos.

    - votos: {nombre_alimento: "me_gusta" | "no_me_gusta"}.
    - Sin votos devuelve {} (el recomendador trata todo como neutro: 0.5).

    Para cada alimento se promedian los votos de los alimentos que se le parecen,
    dándole más importancia a los más parecidos. Un "me gusta" cuenta +1 y un
    "no me gusta" cuenta -1. El SUAVIZADO hace que con pocos votos el puntaje
    quede cerca de 0.5 y que se aleje a medida que hay más votos coherentes.
    """
    if not votos:
        return {}
    vectores = construir_vectores(catalogo)
    votados = [
        (vectores[nombre], 1.0 if voto == config.VOTO_ME_GUSTA else -1.0)
        for nombre, voto in votos.items()
        if nombre in vectores  # se ignoran votos de alimentos que ya no están en el catálogo
    ]
    if not votados:
        return {}

    preferencias: dict[str, float] = {}
    for nombre, vector in vectores.items():
        suma_votos = 0.0
        suma_pesos = 0.0
        for vector_votado, signo in votados:
            parecido = max(0.0, similitud_coseno(vector, vector_votado))  # lo distinto no cuenta
            peso = parecido ** config.EXPONENTE_SIMILITUD
            suma_votos += signo * peso
            suma_pesos += peso
        tendencia = suma_votos / (suma_pesos + config.SUAVIZADO_PREFERENCIA)  # entre -1 y 1
        puntaje = config.PREFERENCIA_NEUTRA + 0.5 * tendencia
        preferencias[nombre] = min(1.0, max(0.0, puntaje))
    return preferencias


def resumir_preferencias(
    catalogo: list[dict],
    preferencias: dict[str, float],
    cantidad: int = config.PREFERENCIAS_DESTACADAS,
) -> dict[str, list[dict]]:
    """Los alimentos que más y menos se recomendarían (solo los que se usan en menús).

    Se omiten los de categoría "otro" y los ingredientes excluidos (ajo, culantro,
    harina), porque el recomendador nunca los usa y confundirían al usuario.
    """
    usables = {
        a["name"] for a in catalogo
        if a["app_category"] in config.CATEGORIAS_APP
        and a["name"] not in config.INGREDIENTES_EXCLUIDOS
    }
    ordenados = sorted(
        ((n, p) for n, p in preferencias.items() if n in usables),
        key=lambda par: (-par[1], par[0]),
    )
    formato = lambda pares: [{"nombre": n, "puntaje": round(p, 3)} for n, p in pares]
    return {
        "mas_recomendados": formato(ordenados[:cantidad]),
        "menos_recomendados": formato(list(reversed(ordenados[-cantidad:]))),
    }
