export type FoodCategory =
  | 'cereales'
  | 'legumbres'
  | 'carnes'
  | 'frutas'
  | 'verduras'
  | 'lacteos'
  | 'otros'

export interface Nutrition {
  /** Valores aproximados por cada 100 g de alimento. */
  calories: number
  protein: number
  carbs: number
  fats: number
  fiber: number
}

export interface Food {
  id: string
  name: string
  category: FoodCategory
  /** Unidad de referencia para el precio, p. ej. "kg", "unidad", "L". */
  unit: string
  /** Precio de referencia aproximado en soles (S/) por unidad. */
  referencePrice: number
  nutrition: Nutrition
}

/**
 * Nutrientes por cantidad de referencia. `null` significa que la fuente no
 * reporta ese dato: nunca debe mostrarse ni sumarse como 0.
 */
export interface CatalogNutrients {
  energyKcal: number | null
  proteinG: number | null
  carbohydrateG: number | null
  fatG: number | null
  fiberG: number | null
  sodiumMg: number | null
  calciumMg: number | null
  ironMg: number | null
}

/** Alimento del catálogo TPCA servido por el backend (`GET /foods`). */
export interface CatalogFood {
  id: string
  name: string
  /** Una de las 11 categorías TPCA, p. ej. "Tubérculos". */
  category: string
  /** Cantidad a la que corresponden los nutrientes, hoy siempre 100 g. */
  referenceAmount: number
  referenceUnit: string
  nutrients: CatalogNutrients
  source: {
    name: string
    version: string
    sourceCode: string
    sourceName: string
  }
}
