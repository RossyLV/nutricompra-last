/**
 * Maps one row of data/nutricompra-foods-v1.csv (TPCA 2023 export) into the
 * three records the seed writes: Food, NutritionalProfile and DataSource.
 */

import { readFileSync } from 'fs';
import { parse } from 'csv-parse/sync';

/** One CSV row as parsed with headers, every value still a raw string. */
export interface TpcaCsvRow {
  id: string;
  name: string;
  category: string;
  type: string;
  reference_amount: string;
  reference_unit: string;
  energy_kcal: string;
  protein_g: string;
  carbohydrate_g: string;
  fat_g: string;
  fiber_g: string;
  sodium_mg: string;
  calcium_mg: string;
  iron_mg: string;
  source: string;
  source_version: string;
  source_code: string;
  source_name: string;
}

export interface TpcaSeedRecord {
  food: { name: string; category: string; type: string };
  profile: {
    referenceAmount: number;
    referenceUnit: string;
    energyKcal: number | null;
    proteinG: number | null;
    carbohydrateG: number | null;
    fatG: number | null;
    fiberG: number | null;
    sodiumMg: number | null;
    calciumMg: number | null;
    ironMg: number | null;
  };
  source: {
    name: string;
    version: string;
    sourceCode: string;
    sourceName: string;
  };
}

/**
 * A blank cell (empty or only spaces) means the source does not report that
 * nutrient, so it maps to null. Number('') and Number(' ') would silently
 * turn it into 0, a different fact. Anything else must be a number: a stray
 * marker such as TPCA's "•" stops the seed instead of being stored.
 */
function toNutrient(
  value: string,
  field: string,
  foodName: string,
): number | null {
  if (value.trim() === '') return null;
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    throw new Error(`Invalid ${field} for "${foodName}": "${value}"`);
  }
  return parsed;
}

export function mapTpcaRow(row: TpcaCsvRow): TpcaSeedRecord {
  const nutrient = (field: keyof TpcaCsvRow) =>
    toNutrient(row[field], field, row.name);

  return {
    food: { name: row.name, category: row.category, type: row.type },
    profile: {
      referenceAmount: Number(row.reference_amount),
      referenceUnit: row.reference_unit,
      energyKcal: nutrient('energy_kcal'),
      proteinG: nutrient('protein_g'),
      carbohydrateG: nutrient('carbohydrate_g'),
      fatG: nutrient('fat_g'),
      fiberG: nutrient('fiber_g'),
      sodiumMg: nutrient('sodium_mg'),
      calciumMg: nutrient('calcium_mg'),
      ironMg: nutrient('iron_mg'),
    },
    source: {
      name: row.source,
      version: row.source_version,
      sourceCode: row.source_code,
      sourceName: row.source_name,
    },
  };
}

/**
 * Reads the whole CSV using its header row as keys. A real parser is needed
 * because source names are quoted and may contain commas.
 */
export function readTpcaCsv(path: string): TpcaSeedRecord[] {
  const rows: TpcaCsvRow[] = parse(readFileSync(path, 'utf8'), {
    columns: true,
  });
  return rows.map(mapTpcaRow);
}
