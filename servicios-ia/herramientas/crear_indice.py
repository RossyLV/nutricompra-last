"""Crea (una sola vez) el índice del catálogo en Microsoft Foundry.

Qué hace:
  1. Lee datos/catalogo.csv.
  2. Lo convierte en texto con etiquetas en español (una línea por alimento).
  3. Lo sube a Foundry y espera a que quede indexado.
  4. Imprime el ID del índice, que se pega en el .env como ID_INDICE_CATALOGO.

Uso (desde la carpeta servicios-ia):
    python herramientas/crear_indice.py

Si ya tienes un ID_INDICE_CATALOGO que funciona, NO hace falta correrlo otra vez
(cada ejecución crea un índice nuevo). Correrlo de nuevo solo se justifica si cambió el catálogo.
"""
import sys
from pathlib import Path

# Permite importar el paquete "app" sin importar desde dónde se ejecute el script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))

from app import catalogo, chat  # noqa: E402


def main() -> int:
    try:
        cliente = chat.crear_cliente()
    except chat.ErrorConfiguracionChat as error:
        print(f"ERROR: {error}")
        return 1

    alimentos = catalogo.cargar_catalogo()
    texto = chat.catalogo_a_texto(alimentos)
    print(f"Catálogo leído: {len(alimentos)} alimentos. Subiendo a Foundry...")

    archivo = cliente.files.create(
        file=("catalogo_nutricompra.txt", texto.encode("utf-8")),
        purpose="assistants",
    )
    indice = cliente.vector_stores.create(name="catalogo-nutricompra")
    cliente.vector_stores.files.create_and_poll(vector_store_id=indice.id, file_id=archivo.id)

    print("Listo. Agrega esta línea a tu archivo servicios-ia/.env:")
    print(f"ID_INDICE_CATALOGO={indice.id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
