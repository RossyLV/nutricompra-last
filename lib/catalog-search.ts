/**
 * Búsqueda del catálogo de la pantalla Nutrición. Vive aparte de la UI para
 * poder moverla al backend cuando el catálogo crezca (ver nota en la épica).
 */

/** Texto comparable: sin tildes ni mayúsculas ("Maíz" y "MAIZ" → "maiz"). */
function normalize(text: string): string {
  return text.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase()
}

/** Elementos cuyo nombre contiene la búsqueda, sin importar tildes ni mayúsculas. */
export function searchByName<T extends { name: string }>(items: T[], query: string): T[] {
  const normalizedQuery = normalize(query.trim())
  return items.filter((item) => normalize(item.name).includes(normalizedQuery))
}

interface FoodFilters {
  query: string
  /** Categoría elegida; `null` o ausente significa "Todas". */
  category?: string | null
}

export function filterFoods<T extends { name: string; category: string }>(
  foods: T[],
  { query, category }: FoodFilters,
): T[] {
  const inCategory = category ? foods.filter((food) => food.category === category) : foods
  return searchByName(inCategory, query)
}

/** Orden alfabético español ("Lácteos" antes que "Legumbres"). */
const spanish = new Intl.Collator('es')

/** Categorías presentes en el catálogo, sin repetir y en orden español. */
export function foodCategories(foods: { category: string }[]): string[] {
  return [...new Set(foods.map((food) => food.category))].sort(spanish.compare)
}
