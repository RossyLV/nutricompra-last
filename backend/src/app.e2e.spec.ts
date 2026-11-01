import { INestApplication } from '@nestjs/common';
import { Test } from '@nestjs/testing';
import * as request from 'supertest';
import { AppModule } from './app.module';
import { setupApp } from './app.setup';
import { PrismaService } from './prisma/prisma.service';

// Boots the real AppModule (not FoodsModule alone) with the same HTTP setup
// main.ts applies, so module wiring and CORS are covered too.
describe('App', () => {
  let app: INestApplication | undefined;

  /** Starts the app after each test has set the environment it needs. */
  async function startApp() {
    const moduleRef = await Test.createTestingModule({
      imports: [AppModule],
    })
      .overrideProvider(PrismaService)
      .useValue({
        nutritionalProfile: { findMany: jest.fn().mockResolvedValue([]) },
      })
      .compile();

    app = moduleRef.createNestApplication();
    setupApp(app);
    await app.init();
    return app;
  }

  beforeEach(() => {
    delete process.env.CORS_ORIGIN;
  });

  afterEach(async () => {
    await app?.close();
    app = undefined;
    delete process.env.CORS_ORIGIN;
  });

  it('expone GET /foods en la app y acepta pedidos del frontend local (CORS)', async () => {
    const server = (await startApp()).getHttpServer();

    const response = await request(server)
      .get('/foods')
      .set('Origin', 'http://localhost:3000')
      .expect(200);

    expect(response.headers['access-control-allow-origin']).toBe(
      'http://localhost:3000',
    );
  });

  it('acepta los sitios de CORS_ORIGIN (producción) y no otros', async () => {
    process.env.CORS_ORIGIN =
      'http://localhost:3000,https://v0-nutricompra-last.vercel.app';
    const server = (await startApp()).getHttpServer();

    const allowed = await request(server)
      .get('/foods')
      .set('Origin', 'https://v0-nutricompra-last.vercel.app')
      .expect(200);
    const other = await request(server)
      .get('/foods')
      .set('Origin', 'https://otro-sitio.example')
      .expect(200);

    expect(allowed.headers['access-control-allow-origin']).toBe(
      'https://v0-nutricompra-last.vercel.app',
    );
    expect(other.headers['access-control-allow-origin']).toBeUndefined();
  });
});
