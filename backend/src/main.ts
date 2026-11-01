import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

// Nest does not read .env by itself; Node's built-in loader does it without
// extra dependencies. A missing file is fine when variables come from the
// host; any other problem (malformed file, unsupported Node) must surface.
try {
  process.loadEnvFile();
} catch (error) {
  if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error;
}

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  // The Next.js frontend runs on :3000 in local development.
  app.enableCors({ origin: 'http://localhost:3000' });
  await app.listen(process.env.PORT ?? 3001);
}
bootstrap();
