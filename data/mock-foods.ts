import type { Food } from '@/types'

/**
 * Catálogo de alimentos con valores nutricionales aproximados por 100 g y
 * precios de referencia ficticios en soles (S/) para Lima, Perú.
 * Los datos son solo demostrativos y no representan precios ni valores reales.
 */
export const mockFoods: Food[] = [
  // Cereales
  {
    id: 'arroz',
    name: 'Arroz',
    category: 'cereales',
    unit: 'kg',
    referencePrice: 3.9,
    nutrition: { calories: 130, protein: 2.7, carbs: 28, fats: 0.3, fiber: 0.4 },
  },
  {
    id: 'avena',
    name: 'Avena',
    category: 'cereales',
    unit: 'kg',
    referencePrice: 6.5,
    nutrition: { calories: 389, protein: 16.9, carbs: 66, fats: 6.9, fiber: 10.6 },
  },
  {
    id: 'fideos',
    name: 'Fideos',
    category: 'cereales',
    unit: 'kg',
    referencePrice: 4.2,
    nutrition: { calories: 158, protein: 5.8, carbs: 31, fats: 0.9, fiber: 1.8 },
  },
  {
    id: 'pan-integral',
    name: 'Pan integral',
    category: 'cereales',
    unit: 'unidad',
    referencePrice: 0.5,
    nutrition: { calories: 247, protein: 13, carbs: 41, fats: 3.4, fiber: 7 },
  },
  {
    id: 'quinua',
    name: 'Quinua',
    category: 'cereales',
    unit: 'kg',
    referencePrice: 12.5,
    nutrition: { calories: 368, protein: 14.1, carbs: 64, fats: 6.1, fiber: 7 },
  },

  // Legumbres
  {
    id: 'lentejas',
    name: 'Lentejas',
    category: 'legumbres',
    unit: 'kg',
    referencePrice: 6.9,
    nutrition: { calories: 116, protein: 9, carbs: 20, fats: 0.4, fiber: 7.9 },
  },
  {
    id: 'frijoles',
    name: 'Frijoles',
    category: 'legumbres',
    unit: 'kg',
    referencePrice: 7.8,
    nutrition: { calories: 127, protein: 8.7, carbs: 23, fats: 0.5, fiber: 6.4 },
  },
  {
    id: 'garbanzos',
    name: 'Garbanzos',
    category: 'legumbres',
    unit: 'kg',
    referencePrice: 8.4,
    nutrition: { calories: 164, protein: 8.9, carbs: 27, fats: 2.6, fiber: 7.6 },
  },
  {
    id: 'arvejas',
    name: 'Arvejas',
    category: 'legumbres',
    unit: 'kg',
    referencePrice: 5.5,
    nutrition: { calories: 81, protein: 5.4, carbs: 14, fats: 0.4, fiber: 5.1 },
  },

  // Carnes y proteínas
  {
    id: 'pollo',
    name: 'Pollo',
    category: 'carnes',
    unit: 'kg',
    referencePrice: 11.5,
    nutrition: { calories: 165, protein: 31, carbs: 0, fats: 3.6, fiber: 0 },
  },
  {
    id: 'huevos',
    name: 'Huevos',
    category: 'carnes',
    unit: 'kg',
    referencePrice: 7.2,
    nutrition: { calories: 155, protein: 13, carbs: 1.1, fats: 11, fiber: 0 },
  },
  {
    id: 'jurel',
    name: 'Jurel',
    category: 'carnes',
    unit: 'kg',
    referencePrice: 9.5,
    nutrition: { calories: 146, protein: 23, carbs: 0, fats: 5, fiber: 0 },
  },
  {
    id: 'carne-res',
    name: 'Carne de res',
    category: 'carnes',
    unit: 'kg',
    referencePrice: 22,
    nutrition: { calories: 250, protein: 26, carbs: 0, fats: 15, fiber: 0 },
  },
  {
    id: 'atun',
    name: 'Atún enlatado',
    category: 'carnes',
    unit: 'unidad',
    referencePrice: 4.5,
    nutrition: { calories: 116, protein: 26, carbs: 0, fats: 1, fiber: 0 },
  },

  // Frutas
  {
    id: 'platano',
    name: 'Plátano',
    category: 'frutas',
    unit: 'kg',
    referencePrice: 3.2,
    nutrition: { calories: 89, protein: 1.1, carbs: 23, fats: 0.3, fiber: 2.6 },
  },
  {
    id: 'manzana',
    name: 'Manzana',
    category: 'frutas',
    unit: 'kg',
    referencePrice: 5.4,
    nutrition: { calories: 52, protein: 0.3, carbs: 14, fats: 0.2, fiber: 2.4 },
  },
  {
    id: 'naranja',
    name: 'Naranja',
    category: 'frutas',
    unit: 'kg',
    referencePrice: 3.6,
    nutrition: { calories: 47, protein: 0.9, carbs: 12, fats: 0.1, fiber: 2.4 },
  },
  {
    id: 'papaya',
    name: 'Papaya',
    category: 'frutas',
    unit: 'kg',
    referencePrice: 3.9,
    nutrition: { calories: 43, protein: 0.5, carbs: 11, fats: 0.3, fiber: 1.7 },
  },

  // Verduras
  {
    id: 'tomate',
    name: 'Tomate',
    category: 'verduras',
    unit: 'kg',
    referencePrice: 3.4,
    nutrition: { calories: 18, protein: 0.9, carbs: 3.9, fats: 0.2, fiber: 1.2 },
  },
  {
    id: 'zanahoria',
    name: 'Zanahoria',
    category: 'verduras',
    unit: 'kg',
    referencePrice: 2.8,
    nutrition: { calories: 41, protein: 0.9, carbs: 10, fats: 0.2, fiber: 2.8 },
  },
  {
    id: 'cebolla',
    name: 'Cebolla',
    category: 'verduras',
    unit: 'kg',
    referencePrice: 2.5,
    nutrition: { calories: 40, protein: 1.1, carbs: 9, fats: 0.1, fiber: 1.7 },
  },
  {
    id: 'papa',
    name: 'Papa',
    category: 'verduras',
    unit: 'kg',
    referencePrice: 2.2,
    nutrition: { calories: 77, protein: 2, carbs: 17, fats: 0.1, fiber: 2.2 },
  },
  {
    id: 'espinaca',
    name: 'Espinaca',
    category: 'verduras',
    unit: 'atado',
    referencePrice: 2,
    nutrition: { calories: 23, protein: 2.9, carbs: 3.6, fats: 0.4, fiber: 2.2 },
  },
  {
    id: 'brocoli',
    name: 'Brócoli',
    category: 'verduras',
    unit: 'kg',
    referencePrice: 4.8,
    nutrition: { calories: 34, protein: 2.8, carbs: 7, fats: 0.4, fiber: 2.6 },
  },

  // Lácteos
  {
    id: 'leche',
    name: 'Leche',
    category: 'lacteos',
    unit: 'L',
    referencePrice: 4.3,
    nutrition: { calories: 61, protein: 3.2, carbs: 4.8, fats: 3.3, fiber: 0 },
  },
  {
    id: 'yogurt',
    name: 'Yogurt',
    category: 'lacteos',
    unit: 'L',
    referencePrice: 6.9,
    nutrition: { calories: 59, protein: 3.5, carbs: 7, fats: 1.5, fiber: 0 },
  },
  {
    id: 'queso-fresco',
    name: 'Queso fresco',
    category: 'lacteos',
    unit: 'kg',
    referencePrice: 18,
    nutrition: { calories: 264, protein: 18, carbs: 3, fats: 20, fiber: 0 },
  },

  // Otros
  {
    id: 'aceite',
    name: 'Aceite vegetal',
    category: 'otros',
    unit: 'L',
    referencePrice: 8.9,
    nutrition: { calories: 884, protein: 0, carbs: 0, fats: 100, fiber: 0 },
  },
  {
    id: 'lecheja',
    name: 'Leche evaporada',
    category: 'otros',
    unit: 'unidad',
    referencePrice: 3.6,
    nutrition: { calories: 134, protein: 6.8, carbs: 10, fats: 7.6, fiber: 0 },
  },
]
