import { INestApplication } from '@nestjs/common';

/** HTTP setup shared by main.ts and the e2e tests. */
export function setupApp(app: INestApplication) {
  // The Next.js frontend runs on :3000 in local development.
  app.enableCors({ origin: 'http://localhost:3000' });
}
