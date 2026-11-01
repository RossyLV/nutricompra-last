import { mockFoods } from '@/data/mock-foods'
import { mockHousehold } from '@/data/mock-households'
import { mockWeekPlan } from '@/data/mock-plan'
import { mockProductPrices } from '@/data/mock-prices'
import { mockUser } from '@/data/mock-users'
import { buildShoppingList } from '@/lib/shopping'
import type {
  CatalogFood,
  Food,
  Household,
  ProductPrice,
  ShoppingList,
  User,
  WeekPlan,
} from '@/types'

/**
 * Capa de acceso a datos del MVP. Todas las funciones son asíncronas para que
 * puedan reemplazarse por llamadas reales a una API o base de datos sin
 * cambiar los componentes que las consumen.
 */

const clone = <T>(value: T): T => structuredClone(value)

export async function getCurrentUser(): Promise<User> {
  return clone(mockUser)
}

export async function getHousehold(): Promise<Household> {
  return clone(mockHousehold)
}

export async function getWeekPlan(): Promise<WeekPlan> {
  return clone(mockWeekPlan)
}

export async function getFoods(): Promise<Food[]> {
  return clone(mockFoods)
}

export async function searchFoods(query: string): Promise<Food[]> {
  const q = query.trim().toLowerCase()
  if (!q) return clone(mockFoods)
  return clone(mockFoods.filter((f) => f.name.toLowerCase().includes(q)))
}

export async function getProductPrices(): Promise<ProductPrice[]> {
  return clone(mockProductPrices)
}

export async function getShoppingList(): Promise<ShoppingList> {
  return clone(buildShoppingList(mockWeekPlan))
}

/**
 * Catálogo de alimentos TPCA con su información nutricional, servido por el
 * backend NestJS. Es la primera función que ya no usa datos de prueba.
 */
export async function getCatalogFoods(): Promise<CatalogFood[]> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL
  if (!apiUrl) {
    throw new Error('Falta NEXT_PUBLIC_API_URL: defínela en .env.local (ver .env.example)')
  }
  const response = await fetch(`${apiUrl}/foods`)
  if (!response.ok) {
    throw new Error(`GET /foods respondió ${response.status}`)
  }
  return response.json()
}
