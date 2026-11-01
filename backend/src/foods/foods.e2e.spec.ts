import { INestApplication } from '@nestjs/common';
import { Test } from '@nestjs/testing';
import { Prisma } from '@prisma/client';
import * as request from 'supertest';
import { PrismaModule } from '../prisma/prisma.module';
import { PrismaService } from '../prisma/prisma.service';
import { FoodsModule } from './foods.module';

const createdAt = new Date('2026-10-30T00:00:00Z');

// What Prisma returns for "Arroz blanco" once seeded: values from the TPCA
// CSV (row id 2), decimals as Prisma.Decimal and the missing fiber as null.
const arrozBlancoProfile = {
  id: 'profile-arroz',
  foodId: 'food-arroz',
  referenceAmount: new Prisma.Decimal('100'),
  referenceUnit: 'g',
  energyKcal: new Prisma.Decimal('358'),
  proteinG: new Prisma.Decimal('7.8'),
  carbohydrateG: new Prisma.Decimal('77.6'),
  fatG: new Prisma.Decimal('0.7'),
  fiberG: null,
  sodiumMg: new Prisma.Decimal('19'),
  calciumMg: new Prisma.Decimal('6'),
  ironMg: new Prisma.Decimal('1.04'),
  dataSourceId: 'source-a3',
  createdAt,
  updatedAt: createdAt,
  food: {
    id: 'food-arroz',
    name: 'Arroz blanco',
    category: 'Cereales',
    type: 'basic',
    createdAt,
    updatedAt: createdAt,
  },
  dataSource: {
    id: 'source-a3',
    name: 'TPCA',
    version: '2023',
    sourceCode: 'A3',
    sourceName: 'Arroz blanco corriente',
    sourceUrl: null,
    notes: null,
    createdAt,
  },
};

/** Same profile shape, for another food of the catalog. */
function profileOf(id: string, name: string, category: string) {
  return {
    ...arrozBlancoProfile,
    foodId: id,
    food: { ...arrozBlancoProfile.food, id, name, category },
  };
}

describe('GET /foods', () => {
  let app: INestApplication;
  let findMany: jest.Mock;

  beforeEach(async () => {
    findMany = jest.fn().mockResolvedValue([arrozBlancoProfile]);
    const moduleRef = await Test.createTestingModule({
      imports: [PrismaModule, FoodsModule],
    })
      .overrideProvider(PrismaService)
      .useValue({ nutritionalProfile: { findMany } })
      .compile();

    app = moduleRef.createNestApplication();
    await app.init();
  });

  afterEach(async () => {
    await app.close();
  });

  it('responde 200 con la lista en el formato acordado (nutrientes y fuente)', async () => {
    const response = await request(app.getHttpServer())
      .get('/foods')
      .expect(200);

    expect(response.body).toHaveLength(1);
    const [food] = response.body;
    expect(Object.keys(food).sort()).toEqual([
      'category',
      'id',
      'name',
      'nutrients',
      'referenceAmount',
      'referenceUnit',
      'source',
    ]);
    expect(food).toMatchObject({
      id: 'food-arroz',
      name: 'Arroz blanco',
      category: 'Cereales',
      referenceUnit: 'g',
      source: {
        name: 'TPCA',
        version: '2023',
        sourceCode: 'A3',
        sourceName: 'Arroz blanco corriente',
      },
    });
    expect(Object.keys(food.nutrients).sort()).toEqual([
      'calciumMg',
      'carbohydrateG',
      'energyKcal',
      'fatG',
      'fiberG',
      'ironMg',
      'proteinG',
      'sodiumMg',
    ]);
  });

  it('devuelve los decimales como números (7.8, no "7.800")', async () => {
    const response = await request(app.getHttpServer())
      .get('/foods')
      .expect(200);

    const [food] = response.body;
    expect(food.referenceAmount).toBe(100);
    expect(food.nutrients).toMatchObject({
      energyKcal: 358,
      proteinG: 7.8,
      carbohydrateG: 77.6,
      fatG: 0.7,
      sodiumMg: 19,
      calciumMg: 6,
      ironMg: 1.04,
    });
  });

  it('devuelve null para los nutrientes sin dato: no 0 ni campo ausente', async () => {
    const response = await request(app.getHttpServer())
      .get('/foods')
      .expect(200);

    const [food] = response.body;
    expect(food.nutrients).toHaveProperty('fiberG', null);
  });

  it('ordena por categoría y nombre según el español (Lácteos antes que Legumbres)', async () => {
    findMany.mockResolvedValueOnce([
      profileOf('food-lentejas', 'Lentejas', 'Legumbres'),
      profileOf('food-yogurt', 'Yogurt', 'Lácteos'),
      profileOf('food-leche', 'Leche fresca entera', 'Lácteos'),
    ]);

    const response = await request(app.getHttpServer())
      .get('/foods')
      .expect(200);

    expect(response.body.map((food: { name: string }) => food.name)).toEqual([
      'Leche fresca entera',
      'Yogurt',
      'Lentejas',
    ]);
  });
});
