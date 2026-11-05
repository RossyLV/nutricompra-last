# servicios-ia — NutriCompra Inteligente

Servicios de IA (Python 3.11) que se conectan al prototipo web:
clasificación de fotos de alimentos, recomendación de menús y dashboard.

> README en construcción: se completa fase por fase.

## Probar localmente (pruebas automáticas)

```bash
cd servicios-ia
python -m venv .venv
# Windows: .venv\Scripts\activate    |  Mac/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

## Levantar la API

La primera vez hay que instalar también el modelo (torch + transformers):

```bash
pip install -r api/requirements.txt
cd api
uvicorn app.main:app --reload
```
Abre http://localhost:8000/docs para probar los endpoints desde el navegador:

| Endpoint | Qué hace |
|---|---|
| `GET /salud` | Comprueba que el servicio está encendido |
| `GET /catalogo` | Lista los 78 alimentos (filtro opcional: `?categoria=proteina`) |
| `GET /catalogo/{nombre}` | Un alimento, por ejemplo `/catalogo/Quinua` |
| `POST /clasificar` | Sube una foto JPG/PNG y devuelve el top-3 con categoría, precio y nutrientes |
| `POST /recomendar` | Con `{"presupuesto": 200, "personas": 4}` arma el menú de 21 comidas, el balance nutricional y la lista de compras |

La primera foto tarda más porque se descarga el modelo `nateraw/food` (unos 350 MB, licencia Apache-2.0).

## Probar el clasificador desde la terminal

```bash
cd servicios-ia
python evaluacion/probar_clasificador.py mi_foto.jpg
python evaluacion/probar_clasificador.py --etiquetas   # revisa las clases del modelo vs. la tabla
```

## Datos

- `datos/catalogo.csv`: los 78 alimentos de la TPCA con las mismas columnas del backend, más
  `price_per_kg_ref` (precio de referencia en soles/kg, **valores aproximados provisionales**) y
  `app_category` (vegetal, carbohidrato, proteina, fruta, lacteo u otro).
- `datos/equivalencias.csv`: las 101 clases de Food-101 → categoría de la app → alimento más
  cercano del catálogo (vacío si no hay uno razonable). Se puede editar con cualquier hoja de cálculo.

Un campo nutricional vacío significa "dato no disponible en la fuente"; nunca se trata como 0.

## Límites conocidos

Food-101 reconoce **platos** (pizza, ceviche, hamburguesa), no ingredientes sueltos ni la mayoría de
platos peruanos. Por eso se mide su precisión en la fase de evaluación.

## Cómo arma el menú el recomendador

Cada comida combina **ingredientes** del catálogo (no hay recetas): desayuno = carbohidrato + lácteo + fruta;
almuerzo y cena = carbohidrato + proteína + vegetal. Se mide el balance diario (energía, proteína, grasa,
calcio y hierro) frente a requerimientos de referencia de un adulto, se parte de un menú barato y se mejora
por intercambios sin pasarse del presupuesto. Reglas de variedad: un ingrediente se repite como máximo 4 veces
por semana y el almuerzo y la cena del mismo día llevan proteínas distintas.

Simplificaciones declaradas: todas las personas comen porción de adulto; los requerimientos son de referencia
general (no una recomendación médica); los datos nutricionales vacíos no se cuentan como 0 y se avisa en la respuesta.
