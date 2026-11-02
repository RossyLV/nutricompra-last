# servicios-ia — NutriCompra Inteligente

Servicios de IA (Python 3.11) que se conectan al prototipo web:
clasificación de fotos de alimentos, recomendación de menús y dashboard.

> README en construcción: se completa fase por fase.

## Probar localmente

```bash
cd servicios-ia
python -m venv .venv
# Windows: .venv\Scripts\activate    |  Mac/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

## Levantar la API (Fase 1)

```bash
cd servicios-ia/api
uvicorn app.main:app --reload
```
Abre http://localhost:8000/docs para probar los endpoints desde el navegador:

| Endpoint | Qué hace |
|---|---|
| `GET /salud` | Comprueba que el servicio está encendido |
| `GET /catalogo` | Lista los 78 alimentos (filtro opcional: `?categoria=proteina`) |
| `GET /catalogo/{nombre}` | Un alimento, por ejemplo `/catalogo/Quinua` |

## Catálogo

`datos/catalogo.csv` tiene los 78 alimentos de la TPCA con las mismas columnas del backend,
más dos columnas propias:

- `price_per_kg_ref`: precio de referencia en soles por kg. **Son valores aproximados
  provisionales**, hasta que el backend tenga precios reales.
- `app_category`: vegetal, carbohidrato, proteina, fruta, lacteo u otro (fuera del balance).

Un campo nutricional vacío significa "dato no disponible en la fuente"; nunca se trata como 0.
