# NutriCompra — Backend

Backend de NutriCompra: NestJS + Prisma + PostgreSQL (Neon), independiente del
frontend Next.js (raíz del repositorio).

Arquitectura y modelo de datos: [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md).

## Quick start

```bash
npm install
cp .env.example .env     # completa DATABASE_URL con tu cadena de conexión de Neon
npx prisma generate      # genera el cliente Prisma tipado
npx prisma migrate deploy  # aplica las migraciones pendientes (no hace nada si ya están)
npm run db:seed          # carga los 78 alimentos TPCA (se puede repetir sin duplicar)
npm run start:dev        # http://localhost:3001
```

El frontend espera el backend en `NEXT_PUBLIC_API_URL` (ver `.env.example` en
la raíz del repositorio). En local, Next.js usa el puerto 3000 y el backend el
3001; CORS acepta por defecto solo `http://localhost:3000` (ver `CORS_ORIGIN`).

## Variables de entorno (`backend/.env`)

| Variable | Uso |
|---|---|
| `DATABASE_URL` | Cadena de conexión PostgreSQL (Neon). Nunca se versiona. |
| `PORT` | Puerto del servidor. Por defecto `3001`. |
| `CORS_ORIGIN` | Sitios que pueden llamar a la API, separados por comas. Por defecto `http://localhost:3000`; en producción, la URL del frontend en Vercel. |

`main.ts` carga `.env` con `process.loadEnvFile()` (incluido en Node).

## Datos: seed TPCA

- Origen: `prisma/data/nutricompra-foods-v1.csv` — 78 alimentos básicos de la
  Tabla Peruana de Composición de Alimentos (TPCA 2023), valores por 100 g.
- `npm run db:seed` guarda cada alimento con su perfil nutricional y su fuente
  mediante upsert, por lo que repetirlo no duplica y completa una carga
  interrumpida. Al terminar imprime los conteos reales (`78 · 78 · 78`).
- Una celda vacía del CSV significa "la fuente no reporta el dato" y se guarda
  como `NULL`, nunca como `0`.

## API

### `GET /foods`

Lista de alimentos ordenada por categoría y nombre (orden alfabético español).

```json
[
  {
    "id": "uuid",
    "name": "Arroz blanco",
    "category": "Cereales",
    "referenceAmount": 100,
    "referenceUnit": "g",
    "nutrients": {
      "energyKcal": 358, "proteinG": 7.8, "carbohydrateG": 77.6, "fatG": 0.7,
      "fiberG": null, "sodiumMg": 19, "calciumMg": 6, "ironMg": 1.04
    },
    "source": {
      "name": "TPCA", "version": "2023",
      "sourceCode": "A3", "sourceName": "Arroz blanco corriente"
    }
  }
]
```

Los nutrientes son números; `null` indica que la fuente no reporta el dato.

## Scripts

| Script | Qué hace |
|---|---|
| `npm run start:dev` | Servidor en modo watch |
| `npm run build` / `npm run start:prod` | Build y ejecución de producción |
| `npm test` | Tests (Jest): seed del CSV y `GET /foods` con Prisma simulado |
| `npm run db:seed` | Carga los alimentos TPCA en la base |
| `npm run prisma:studio` | Explorador visual de la base |
