"""Script para probar el clasificador REAL (descarga el modelo la primera vez).

Uso, desde la carpeta servicios-ia:

  python evaluacion/probar_clasificador.py foto.jpg      -> top-3 de una foto
  python evaluacion/probar_clasificador.py --etiquetas   -> revisa que las clases del
                                                            modelo estén en equivalencias.csv
"""
import sys
from pathlib import Path

# Permite importar el paquete "app" que vive en servicios-ia/api
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))

from app import catalogo as cat  # noqa: E402
from app import clasificador, config  # noqa: E402


def revisar_etiquetas() -> None:
    """Compara las clases que conoce el modelo con las de equivalencias.csv."""
    from transformers import AutoConfig

    configuracion = AutoConfig.from_pretrained(config.MODELO_HF)
    del_modelo = {clasificador.normalizar_etiqueta(e) for e in configuracion.id2label.values()}
    equivalencias = clasificador.cargar_equivalencias(catalogo=cat.cargar_catalogo())
    de_la_tabla = set(equivalencias)

    print(f"Clases del modelo: {len(del_modelo)} | clases en la tabla: {len(de_la_tabla)}")
    sin_mapear = sorted(del_modelo - de_la_tabla)
    sobrantes = sorted(de_la_tabla - del_modelo)
    print("Clases del modelo SIN fila en la tabla:", sin_mapear or "ninguna")
    print("Filas de la tabla que el modelo NO tiene:", sobrantes or "ninguna")


def probar_foto(ruta: str) -> None:
    """Clasifica una foto del disco e imprime el top-3."""
    contenido = Path(ruta).read_bytes()
    tipo = "image/png" if ruta.lower().endswith(".png") else "image/jpeg"
    catalogo = cat.cargar_catalogo()
    resultado = clasificador.clasificar_imagen(
        contenido, tipo, clasificador.obtener_predictor(), catalogo,
        clasificador.cargar_equivalencias(catalogo=catalogo),
    )
    print(resultado["mensaje"])
    for p in resultado["predicciones"]:
        alimento = p["alimento"]["name"] if p["alimento"] else "(sin alimento en catálogo)"
        print(f"  {p['probabilidad']:.1%}  {p['nombre']:<30} {str(p['categoria']):<13} {alimento}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
    elif sys.argv[1] == "--etiquetas":
        revisar_etiquetas()
    else:
        probar_foto(sys.argv[1])
