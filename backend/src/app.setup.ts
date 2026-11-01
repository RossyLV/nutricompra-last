import { INestApplication } from '@nestjs/common';

/** HTTP setup shared by main.ts and the e2e tests. */
export function setupApp(app: INestApplication) {
  // Sites allowed to call the API, comma-separated (e.g. the Vercel frontend).
  // Defaults to the Next.js dev server for local development.
  const origins = (process.env.CORS_ORIGIN ?? 'http://localhost:3000')
    .split(',')
    .map((origin) => origin.trim())
    .filter(Boolean);
  app.enableCors({ origin: origins });
}
