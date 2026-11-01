/**
 * Loads the 78 TPCA foods from data/nutricompra-foods-v1.csv into the
 * database (Food + NutritionalProfile + DataSource).
 *
 * Safe to re-run: every write is an upsert, so a second run updates rows
 * instead of duplicating them, and re-running finishes an interrupted run.
 * That is why it does not use a transaction.
 *
 * Usage: npm run db:seed
 */
import { join } from 'path';
import { PrismaClient } from '@prisma/client';
import { readTpcaCsv } from './seed/tpca-csv';

const prisma = new PrismaClient();
const csvPath = join(__dirname, 'data', 'nutricompra-foods-v1.csv');

async function main() {
  const records = readTpcaCsv(csvPath);

  for (const { food, profile, source } of records) {
    // DataSource has no unique key, so look it up by its natural identity.
    const existingSource = await prisma.dataSource.findFirst({
      where: {
        name: source.name,
        version: source.version,
        sourceCode: source.sourceCode,
      },
    });
    const dataSource = existingSource
      ? await prisma.dataSource.update({
          where: { id: existingSource.id },
          data: source,
        })
      : await prisma.dataSource.create({ data: source });

    const savedFood = await prisma.food.upsert({
      where: { name: food.name },
      update: food,
      create: food,
    });

    await prisma.nutritionalProfile.upsert({
      where: { foodId: savedFood.id },
      update: { ...profile, dataSourceId: dataSource.id },
      create: { ...profile, foodId: savedFood.id, dataSourceId: dataSource.id },
    });
  }

  const [foods, profiles, sources] = await Promise.all([
    prisma.food.count(),
    prisma.nutritionalProfile.count(),
    prisma.dataSource.count(),
  ]);
  console.log(
    `foods: ${foods} · nutritional_profiles: ${profiles} · data_sources: ${sources}`,
  );
}

main()
  .catch((error) => {
    console.error(error);
    process.exitCode = 1;
  })
  .finally(() => prisma.$disconnect());
