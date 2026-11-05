"""Prueba rápida del chat contra Foundry (gasta un poco de crédito: una consulta).

Pregunta por un alimento y muestra, al lado, los valores reales del catálogo para
que compares a ojo si el asistente está usando el catálogo.

Uso (desde la carpeta servicios-ia):
    python herramientas/probar_chat.py Kiwicha
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))

from app import catalogo, chat  # noqa: E402


def main() -> int:
    nombre = " ".join(sys.argv[1:]).strip() or "Kiwicha"
    alimento = catalogo.buscar_alimento(catalogo.cargar_catalogo(), nombre)
    if alimento is None:
        print(f"'{nombre}' no está en el catálogo. Prueba con un nombre exacto de datos/catalogo.csv.")
        return 1

    try:
        servicio = chat.obtener_servicio()
    except chat.ErrorConfiguracionChat as error:
        print(f"ERROR: {error}")
        return 1

    pregunta = f"¿Cuántas calorías, proteína y hierro tiene {alimento['name']} y cuánto cuesta por kg?"
    print(f"Pregunta: {pregunta}\n")
    try:
        resultado = servicio.responder(pregunta, [])
    except chat.ErrorChat as error:
        print(f"ERROR: {error}  (mira el detalle en esta misma ventana si aparece arriba)")
        return 1

    print("Respuesta del asistente:")
    print(resultado["respuesta"])
    print("\nValores reales del catálogo (compáralos):")
    print(
        f"  energía {alimento['energy_kcal']} kcal | proteína {alimento['protein_g']} g | "
        f"hierro {alimento['iron_mg']} mg | precio S/ {alimento['price_per_kg_ref']} por kg"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
