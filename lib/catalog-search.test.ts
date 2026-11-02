import { describe, expect, it } from 'vitest'
import { filterFoods, foodCategories, searchByName } from './catalog-search'

// Alimentos reales del catálogo TPCA (nombre y categoría tal como los entrega GET /foods).
const foods = [
  { name: 'Ajo', category: 'Verduras' },
  { name: 'Ajonjolí', category: 'Grasas' },
  { name: 'Arroz blanco', category: 'Cereales' },
  { name: 'Maíz amarillo', category: 'Cereales' },
  { name: 'Oca', category: 'Tubérculos' },
  { name: 'Papa amarilla', category: 'Tubérculos' },
]

describe('filterFoods', () => {
  it('ignora tildes y mayúsculas: "maiz", "MAIZ" y "ajonjoli" encuentran "Maíz amarillo" y "Ajonjolí"', () => {
    const names = (query: string) => filterFoods(foods, { query }).map((food) => food.name)

    expect(names('maiz')).toEqual(['Maíz amarillo'])
    expect(names('MAIZ')).toEqual(['Maíz amarillo'])
    expect(names('ajonjoli')).toEqual(['Ajonjolí'])
  })

  it('trata la ñ como n a propósito: "pina" encuentra "Piña"', () => {
    // Decisión de producto (revisión de SP-19/SP-20): se prefiere encontrar sin tildes ni ñ.
    expect(searchByName([{ name: 'Piña' }, { name: 'Papaya' }], 'pina').map((item) => item.name)).toEqual(['Piña'])
  })

  it('filtra por categoría: solo devuelve alimentos de la categoría elegida', () => {
    const result = filterFoods(foods, { query: '', category: 'Tubérculos' })

    expect(result.map((food) => food.name)).toEqual(['Oca', 'Papa amarilla'])
  })

  it('combina categoría y búsqueda: busca solo dentro de la categoría elegida', () => {
    // "ar" aparece en Arroz blanco, Maíz amarillo y Papa amarilla; solo la papa es tubérculo.
    const result = filterFoods(foods, { query: 'ar', category: 'Tubérculos' })

    expect(result.map((food) => food.name)).toEqual(['Papa amarilla'])
  })

  it('"Todas" no filtra por categoría', () => {
    // En la pantalla, "Todas" es no tener ninguna categoría elegida (null).
    const result = filterFoods(foods, { query: '', category: null })

    expect(result).toEqual(foods)
  })

  it('una búsqueda vacía o con solo espacios devuelve todo', () => {
    expect(filterFoods(foods, { query: '' })).toEqual(foods)
    expect(filterFoods(foods, { query: '   ' })).toEqual(foods)
  })

  it('devuelve una lista vacía cuando no hay coincidencias', () => {
    expect(filterFoods(foods, { query: 'quinua' })).toEqual([])
    expect(filterFoods(foods, { query: 'oca', category: 'Cereales' })).toEqual([])
  })
})

describe('searchByName', () => {
  it('la búsqueda de comidas ignora tildes: "atun" encuentra "Ensalada de atún con papa"', () => {
    // Comidas reales del plan (data/mock-meals.ts).
    const meals = [
      { name: 'Arroz con pollo y ensalada' },
      { name: 'Ensalada de atún con papa' },
      { name: 'Jurel sudado con papa' },
    ]

    expect(searchByName(meals, 'atun').map((meal) => meal.name)).toEqual(['Ensalada de atún con papa'])
  })
})

describe('foodCategories', () => {
  it('la lista de categorías no repite y va en orden español (Lácteos antes que Legumbres)', () => {
    const catalog = [
      { name: 'Lentejas', category: 'Legumbres' },
      { name: 'Yogurt', category: 'Lácteos' },
      { name: 'Pollo', category: 'Carnes' },
      { name: 'Queso fresco', category: 'Lácteos' },
    ]

    expect(foodCategories(catalog)).toEqual(['Carnes', 'Lácteos', 'Legumbres'])
  })
})
