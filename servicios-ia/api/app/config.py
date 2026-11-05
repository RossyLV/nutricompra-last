"""Configuración central de los servicios de IA de NutriCompra.

Aquí se leen las variables de entorno (nada de secretos en el código)
y se definen las constantes que usa el resto del sistema.
"""
import os
from pathlib import Path

# Carpeta "servicios-ia" (dos niveles arriba de este archivo: app -> api -> servicios-ia)
DIRECTORIO_BASE: Path = Path(__file__).resolve().parents[2]


def _resolver_ruta(ruta: str) -> Path:
    """Convierte una ruta relativa en absoluta, partiendo de servicios-ia.

    Así los archivos de datos se encuentran sin importar desde dónde se ejecute el programa.
    """
    camino = Path(ruta)
    return camino if camino.is_absolute() else DIRECTORIO_BASE / camino


def _leer_entero_positivo(nombre: str, por_defecto: int) -> int:
    """Lee una variable de entorno como entero mayor que cero.

    Si no existe, está vacía o no es válida, devuelve el valor por defecto.
    """
    valor = os.getenv(nombre, "")
    try:
        numero = int(valor)
    except ValueError:
        return por_defecto
    return numero if numero > 0 else por_defecto


def cargar_env(ruta: Path) -> None:
    """Lee un archivo .env (líneas CLAVE=valor) y las deja como variables de entorno.

    - Ignora líneas vacías y comentarios (#).
    - NO pisa las variables que ya existen en el entorno (por ejemplo las de Docker o CI).
    - Si el archivo no existe, no hace nada.
    """
    if not ruta.is_file():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        nombre, valor = linea.split("=", 1)
        nombre = nombre.strip()
        valor = valor.strip().strip('"').strip("'")
        if nombre:
            os.environ.setdefault(nombre, valor)


# El .env vive en servicios-ia/ y NO se sube a GitHub (guarda claves).
cargar_env(DIRECTORIO_BASE / ".env")

# --- Valores que vienen del entorno (.env) con un valor por defecto ---
ENTORNO: str = os.getenv("ENTORNO", "desarrollo")
MODELO_HF: str = os.getenv("MODELO_HF", "nateraw/food")
RUTA_CATALOGO: Path = _resolver_ruta(os.getenv("RUTA_CATALOGO", "datos/catalogo.csv"))
RUTA_EQUIVALENCIAS: Path = _resolver_ruta(
    os.getenv("RUTA_EQUIVALENCIAS", "datos/equivalencias.csv")
)
TAMANO_MAX_IMAGEN_MB: int = _leer_entero_positivo("TAMANO_MAX_IMAGEN_MB", 5)
# Base de datos (SQLite) donde se guardan los "me gusta / no me gusta" (Fase 4).
RUTA_BASE_DATOS: Path = _resolver_ruta(os.getenv("RUTA_BASE_DATOS", "datos/preferencias.db"))

# --- Chat con un modelo de Microsoft Foundry (Fase 5). Las claves SOLO vienen del .env ---
CHAT_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
CHAT_CLAVE: str = os.getenv("AZURE_OPENAI_API_KEY", "")
CHAT_MODELO: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini")  # nombre del despliegue
CHAT_ID_INDICE: str = os.getenv("ID_INDICE_CATALOGO", "")  # lo imprime herramientas/crear_indice.py
CHAT_MAX_TOKENS_SALIDA: int = _leer_entero_positivo("CHAT_MAX_TOKENS_SALIDA", 2000)
CHAT_TIEMPO_ESPERA_S: int = 60
# Límites de lo que se acepta del usuario en el chat.
CHAT_MENSAJE_MAX_LARGO: int = 500
CHAT_HISTORIAL_MAX_MENSAJES: int = 10
CHAT_HISTORIAL_MAX_LARGO: int = 2000
ROLES_CHAT: tuple[str, ...] = ("user", "assistant")
# Personalización: cuántos alimentos de cada lista se le cuentan al modelo (para no inflar la consulta).
CHAT_PERFIL_MAX_ALIMENTOS: int = 10

# --- Constantes fijas del dominio ---
# Las 5 categorías que usa la aplicación para el balance nutricional.
CATEGORIAS_APP: tuple[str, ...] = (
    "vegetal",
    "carbohidrato",
    "proteina",
    "fruta",
    "lacteo",
)
# Alimentos que están en el catálogo pero no cuentan para el balance
# (aceites, semillas, azúcar, postres).
CATEGORIA_OTRO: str = "otro"
CATEGORIAS_CATALOGO: tuple[str, ...] = CATEGORIAS_APP + (CATEGORIA_OTRO,)

# Comidas de un menú semanal: 7 días x 3 comidas.
DIAS_SEMANA: int = 7
COMIDAS_POR_DIA: int = 3
TOTAL_COMIDAS_SEMANA: int = DIAS_SEMANA * COMIDAS_POR_DIA  # 21

# Límites razonables para validar lo que escribe el usuario.
PRESUPUESTO_MAXIMO: float = 100_000.0  # soles por semana
PERSONAS_MAXIMO: int = 20

# Formatos de imagen aceptados al subir una foto (tipo MIME y formato real).
FORMATOS_IMAGEN_PERMITIDOS: tuple[str, ...] = ("image/jpeg", "image/png")
FORMATOS_REALES_PERMITIDOS: tuple[str, ...] = ("JPEG", "PNG")

# Clasificador de imágenes
CANTIDAD_PREDICCIONES: int = 3      # se devuelven las 3 más probables (top-3)
UMBRAL_CONFIANZA: float = 0.40      # por debajo de esto se avisa "poca confianza"

# ---------------------------------------------------------------------------
# Recomendador de menús (Fase 3)
# ---------------------------------------------------------------------------
# Momentos del día y de qué categorías se arma cada comida.
# Cada comida es una combinación de INGREDIENTES del catálogo (no hay recetas).
MOMENTOS_DEL_DIA: tuple[str, ...] = ("desayuno", "almuerzo", "cena")
ESTRUCTURA_COMIDAS: dict[str, tuple[str, ...]] = {
    "desayuno": ("carbohidrato", "lacteo", "fruta"),
    "almuerzo": ("carbohidrato", "proteina", "vegetal"),
    "cena": ("carbohidrato", "proteina", "vegetal"),
}

# Porción por persona de cada categoría, en gramos (peso crudo). Simplificación:
# todas las personas del hogar comen la misma porción de adulto.
PORCIONES_G: dict[str, int] = {
    "carbohidrato": 120,
    "proteina": 120,
    "vegetal": 100,
    "fruta": 150,
    "lacteo": 200,
}

# Excepciones de porción (por persona, en gramos): alimentos que se comen en
# cantidades distintas a las de su categoría. Se busca primero por nombre y
# luego por la categoría original de la TPCA.
PORCIONES_ESPECIALES_POR_NOMBRE_G: dict[str, int] = {
    "Queso fresco": 40,
    "Queso fresco de cabra": 40,
    "Leche evaporada entera": 100,
    "Leche evaporada descremada": 100,
}
PORCIONES_ESPECIALES_POR_TPCA_G: dict[str, int] = {"Legumbres": 80}  # secas

# Ingredientes que están en el catálogo pero no se usan como base de una comida:
# condimentos (ajo, culantro) y la harina de trigo (no se come sola; el fideo ya cubre la pasta).
INGREDIENTES_EXCLUIDOS: tuple[str, ...] = ("Ajo", "Culantro", "Harina de trigo")

# Requerimientos nutricionales DIARIOS de referencia para un adulto, por persona.
# tipo "minimo": basta con llegar a "min" (pasarse no se penaliza).
# tipo "rango": lo ideal es estar entre "min" y "max".
# Son valores de referencia generales, NO una recomendación médica individual.
REQUERIMIENTOS: dict[str, dict] = {
    "energy_kcal": {"nombre": "Energía (kcal)", "tipo": "rango", "min": 1800, "max": 2400},
    "protein_g": {"nombre": "Proteína (g)", "tipo": "minimo", "min": 50},
    "fat_g": {"nombre": "Grasa (g)", "tipo": "rango", "min": 44, "max": 78},
    "calcium_mg": {"nombre": "Calcio (mg)", "tipo": "minimo", "min": 1000},
    "iron_mg": {"nombre": "Hierro (mg)", "tipo": "minimo", "min": 12},
}
NUTRIENTES_BALANCE: tuple[str, ...] = tuple(REQUERIMIENTOS)

# Reglas de variedad del menú
MAX_REPETICIONES_SEMANA: int = 4   # un mismo ingrediente, máximo 4 veces por semana

# Búsqueda del mejor menú (mejora por intercambios)
ITERACIONES_BUSQUEDA: int = 3000
SEMILLA_POR_DEFECTO: int = 42      # misma semilla = mismo menú (resultados repetibles)

# Pesos de la función objetivo (qué tanto importa cada cosa)
PESO_VARIEDAD: float = 0.05
PESO_PREFERENCIA: float = 1.2
PESO_COSTO: float = 0.02           # a igual nutrición, se prefiere el menú más barato
PREFERENCIA_NEUTRA: float = 0.5    # puntaje de un alimento sin "me gusta" ni "no me gusta"

# ---------------------------------------------------------------------------
# Preferencias del usuario: "me gusta / no me gusta" (Fase 4)
# ---------------------------------------------------------------------------
VOTO_ME_GUSTA: str = "me_gusta"
VOTO_NO_ME_GUSTA: str = "no_me_gusta"
VOTOS_VALIDOS: tuple[str, ...] = (VOTO_ME_GUSTA, VOTO_NO_ME_GUSTA)
USUARIO_ID_MAX_LARGO: int = 50

# Características con las que se "describe" cada alimento para medir qué tanto
# se parece a otro. Los nutrientes son los valores por 100 g del catálogo.
NUTRIENTES_CONTENIDO: tuple[str, ...] = (
    "energy_kcal",
    "protein_g",
    "carbohydrate_g",
    "fat_g",
    "calcium_mg",
    "iron_mg",
)
# Qué tanto pesa cada grupo de características al medir el parecido (suman 1).
PESOS_CARACTERISTICAS: dict[str, float] = {"categoria": 0.10, "nutrientes": 0.70, "precio": 0.20}

# Cómo se convierte el parecido en puntaje de preferencia:
# - EXPONENTE_SIMILITUD: mientras más alto, solo cuentan los alimentos MUY parecidos.
# - SUAVIZADO_PREFERENCIA: "evidencia mínima". Con pocos votos parecidos el puntaje
#   se queda cerca de neutro; con más votos coherentes se aleja más.
EXPONENTE_SIMILITUD: int = 8
SUAVIZADO_PREFERENCIA: float = 0.5
PREFERENCIAS_DESTACADAS: int = 5   # cuántos alimentos mostrar en "más / menos recomendados"
