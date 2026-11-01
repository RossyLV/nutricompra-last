import { INestApplication } from '@nestjs/common';
import { Test } from '@nestjs/testing';
import * as request from 'supertest';
import { AppModule } from './app.module';
import { setupApp } from './app.setup';
import { PrismaService } from './prisma/prisma.service';

// Boots the real AppModule (not FoodsModule alone) with the same HTTP setup
// main.ts applies, so module wiring and CORS are covered too.
describe('App', () => {
  let app: INestApplication;

  beforeEach(async () => {
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
  });

  afterEach(async () => {
    await app.close();
  });

  it('expone GET /foods en la app y acepta pedidos del frontend local (CORS)', async () => {
    const response = await request(app.getHttpServer())
      .get('/foods')
      .set('Origin', 'http://localhost:3000')
      .expect(200);

    expect(response.headers['access-control-allow-origin']).toBe(
      'http://localhost:3000',
    );
  });
});
