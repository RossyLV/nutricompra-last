'use client'

import { useMemo, useState } from 'react'
import { Apple, Beef, Carrot, ChevronRight, CircleDot, Egg, Fish, Menu, Search, Wheat, type LucideIcon } from 'lucide-react'
import { AppSidebar } from '@/components/app/app-sidebar'
import { Button } from '@/components/ui/button'
import { mockMeals } from '@/data/mock-meals'
import { mealTypeLabels } from '@/data/mock-plan'
import { useCatalogFoods } from '@/hooks/use-catalog-foods'
import { usePlan } from '@/hooks/use-plan'
import { dayNutrition } from '@/lib/nutrition'
import type { CatalogFood, Meal } from '@/types'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

const nutritionItems = [
  { key: 'calories', label: 'Calorías', unit: 'kcal', color: 'bg-amber-500' },
  { key: 'protein', label: 'Proteínas', unit: 'g', color: 'bg-emerald-500' },
  { key: 'carbs', label: 'Carbohidratos', unit: 'g', color: 'bg-sky-500' },
  { key: 'fats', label: 'Grasas', unit: 'g', color: 'bg-violet-500' },
  { key: 'fiber', label: 'Fibra', unit: 'g', color: 'bg-orange-500' },
] as const

/** Valores de la grilla; `null` = la fuente no reporta el dato (nunca 0). */
type NutritionValues = Record<(typeof nutritionItems)[number]['key'], number | null>

/**
 * Íconos para las categorías TPCA; las que no tienen uno propio usan el
 * genérico. Es un Map porque la categoría es texto libre de la base: en un
 * objeto, nombres como "constructor" devolverían algo que no es un ícono.
 */
const categoryIcons = new Map<string, LucideIcon>([
  ['Cereales', Wheat],
  ['Legumbres', CircleDot],
  ['Carnes', Beef],
  ['Frutas', Apple],
  ['Verduras', Carrot],
  ['Lácteos', CircleDot],
  ['Pescados', Fish],
  ['Huevos', Egg],
])

/** Respuesta inmediata al presionar, sin animación si el sistema pide reducir movimiento. */
const pressableClass =
  'transition-[transform,background-color,border-color] duration-100 ease-out active:scale-[0.98] motion-reduce:transition-none motion-reduce:active:scale-100 outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2'

function catalogNutritionValues(food: CatalogFood): NutritionValues {
  return {
    calories: food.nutrients.energyKcal,
    protein: food.nutrients.proteinG,
    carbs: food.nutrients.carbohydrateG,
    fats: food.nutrients.fatG,
    fiber: food.nutrients.fiberG,
  }
}

function NutritionGrid({ nutrition }: { nutrition: NutritionValues }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
      {nutritionItems.map((item) => {
        const value = nutrition[item.key]
        return (
          <div key={item.key} className="rounded-xl bg-muted/50 p-3">
            <div className="mb-2 flex items-center gap-2">
              <span className={`size-2 rounded-full ${item.color}`} aria-hidden="true" />
              <span className="text-xs text-muted-foreground">{item.label}</span>
            </div>
            <p className="text-lg font-semibold tracking-tight tabular-nums">
              {value === null ? (
                <span className="text-sm font-medium tracking-normal text-muted-foreground">Sin dato</span>
              ) : (
                <>
                  {Math.round(value * 10) / 10} <span className="text-xs font-normal text-muted-foreground">{item.unit}</span>
                </>
              )}
            </p>
          </div>
        )
      })}
    </div>
  )
}

function FoodResult({ food, selected, onSelect }: { food: CatalogFood; selected: boolean; onSelect: () => void }) {
  const Icon = categoryIcons.get(food.category) ?? CircleDot
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`flex w-full items-center gap-3 rounded-xl border p-3 text-left hover:bg-muted/60 ${pressableClass} ${selected ? 'border-primary bg-primary/5' : 'border-border/70'}`}
      aria-pressed={selected}
    >
      <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary"><Icon data-icon="inline-start" /></span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium">{food.name}</span>
        <span className="block text-xs text-muted-foreground">{food.category} · por {food.referenceAmount} {food.referenceUnit}</span>
      </span>
      <ChevronRight className="size-4 text-muted-foreground" aria-hidden="true" />
    </button>
  )
}

function MealResult({ meal, selected, onSelect }: { meal: Meal; selected: boolean; onSelect: () => void }) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`flex w-full items-center gap-3 rounded-xl border p-3 text-left hover:bg-muted/60 ${pressableClass} ${selected ? 'border-primary bg-primary/5' : 'border-border/70'}`}
      aria-pressed={selected}
    >
      <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-secondary text-secondary-foreground"><Apple data-icon="inline-start" /></span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium">{meal.name}</span>
        <span className="block text-xs text-muted-foreground">{mealTypeLabels[meal.type]} · porción individual</span>
      </span>
      <ChevronRight className="size-4 text-muted-foreground" aria-hidden="true" />
    </button>
  )
}

export default function NutritionPage() {
  const { plan } = usePlan()
  const catalog = useCatalogFoods()
  const [query, setQuery] = useState('')
  const [selectedId, setSelectedId] = useState('arroz-pollo')
  const [selectedKind, setSelectedKind] = useState<'food' | 'meal'>('meal')

  const catalogFoods = useMemo(() => (catalog.status === 'ready' ? catalog.foods : []), [catalog])

  const results = useMemo(() => {
    const normalized = query.trim().toLowerCase()
    const foods = catalogFoods.filter((food) => !normalized || food.name.toLowerCase().includes(normalized))
    const meals = mockMeals.filter((meal) => !normalized || meal.name.toLowerCase().includes(normalized))
    return { foods, meals }
  }, [query, catalogFoods])

  const selectedFood = selectedKind === 'food' ? catalogFoods.find((food) => food.id === selectedId) : undefined
  const selectedMeal = selectedKind === 'meal' ? mockMeals.find((meal) => meal.id === selectedId) : undefined
  const selectedNutrition = selectedFood ? catalogNutritionValues(selectedFood) : selectedMeal?.nutrition
  const weeklyAverage = useMemo(() => {
    const total = plan.days.reduce((acc, day) => ({
      calories: acc.calories + dayNutrition(day).calories,
      protein: acc.protein + dayNutrition(day).protein,
      carbs: acc.carbs + dayNutrition(day).carbs,
      fats: acc.fats + dayNutrition(day).fats,
      fiber: acc.fiber + dayNutrition(day).fiber,
    }), { calories: 0, protein: 0, carbs: 0, fats: 0, fiber: 0 })
    const days = plan.days.length || 1
    return { calories: total.calories / days, protein: total.protein / days, carbs: total.carbs / days, fats: total.fats / days, fiber: total.fiber / days }
  }, [plan])

  return (
    <div className="min-h-screen bg-muted/30">
      <AppSidebar />
      <main className="lg:pl-64">
        <header className="border-b bg-background/90 px-5 py-5 backdrop-blur lg:px-10">
          <div className="mx-auto flex max-w-7xl items-center gap-3">
            <Button variant="outline" size="icon" className="lg:hidden" aria-label="Abrir menú">
              <Menu data-icon="inline-start" />
            </Button>
            <div>
              <p className="text-sm font-medium text-primary">Decisiones más informadas</p>
              <h1 className="font-heading text-2xl font-bold tracking-tight sm:text-3xl">Información nutricional</h1>
            </div>
          </div>
        </header>

        <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-5 py-7 lg:px-10 lg:py-9">
          <div>
            <p className="text-sm font-medium text-primary">Consulta y compara</p>
            <h2 className="mt-1 font-heading text-xl font-bold tracking-tight">Planifica con mejor información</h2>
            <p className="mt-2 max-w-2xl text-muted-foreground">Consulta los nutrientes de tus alimentos y comidas para planificar mejor tu semana.</p>
          </div>

          <div className="grid gap-6 lg:grid-cols-[minmax(260px,0.8fr)_minmax(0,1.6fr)]">
        <Card className="h-fit">
          <CardHeader>
            <CardTitle>Buscar alimento o comida</CardTitle>
            <CardDescription>Los alimentos se muestran por cada 100 g.</CardDescription>
            <div className="relative mt-3">
              <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
              <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ej. arroz, lentejas..." aria-label="Buscar alimento o comida" className="pl-9" />
            </div>
          </CardHeader>
          <CardContent className="flex max-h-[520px] flex-col gap-5 overflow-y-auto">
            <section aria-labelledby="foods-heading" aria-busy={catalog.status === 'loading'}>
              <h2 id="foods-heading" className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Alimentos{catalog.status === 'ready' ? ` (${results.foods.length})` : ''}</h2>
              {/* Región viva que existe desde el inicio: los lectores de pantalla anuncian cuando su texto cambia. */}
              <p role="status" className="sr-only">{catalog.status === 'loading' ? 'Cargando alimentos…' : catalog.status === 'ready' ? `${catalogFoods.length} alimentos disponibles` : ''}</p>
              {catalog.status === 'loading' && <p aria-hidden="true" className="rounded-xl border border-dashed p-3 text-sm text-muted-foreground">Cargando alimentos…</p>}
              {catalog.status === 'error' && <p role="alert" className="rounded-xl border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">No se pudieron cargar los alimentos</p>}
              {catalog.status === 'ready' && <div className="flex flex-col gap-2">{results.foods.map((food) => <FoodResult key={food.id} food={food} selected={selectedKind === 'food' && selectedId === food.id} onSelect={() => { setSelectedKind('food'); setSelectedId(food.id) }} />)}</div>}
            </section>
            <section aria-labelledby="meals-heading">
              <h2 id="meals-heading" className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Comidas ({results.meals.length})</h2>
              <div className="flex flex-col gap-2">{results.meals.map((meal) => <MealResult key={meal.id} meal={meal} selected={selectedKind === 'meal' && selectedId === meal.id} onSelect={() => { setSelectedKind('meal'); setSelectedId(meal.id) }} />)}</div>
            </section>
          </CardContent>
        </Card>

        <div className="flex flex-col gap-6">
          <Card>
            <CardHeader>
              <CardDescription>{selectedFood ? `${selectedFood.category} · referencia por ${selectedFood.referenceAmount} ${selectedFood.referenceUnit}` : 'Comida completa · porción individual'}</CardDescription>
              <CardTitle className="text-2xl">{selectedFood?.name ?? selectedMeal?.name ?? 'Selecciona una opción'}</CardTitle>
            </CardHeader>
            <CardContent>{selectedNutrition ? <NutritionGrid nutrition={selectedNutrition} /> : <p className="text-muted-foreground">Selecciona un alimento o comida para ver sus datos.</p>}</CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Promedio diario de tu plan</CardTitle><CardDescription>Resumen calculado a partir de las comidas de esta semana.</CardDescription></CardHeader>
            <CardContent><NutritionGrid nutrition={weeklyAverage} /></CardContent>
          </Card>

          <Card className="border-primary/20 bg-primary/5">
            <CardHeader><CardTitle>Usa esta información para planificar</CardTitle><CardDescription>Compara opciones del menú y elige las que mejor se ajusten a tus preferencias y presupuesto.</CardDescription></CardHeader>
            <CardContent><p className="text-sm text-muted-foreground">Los valores son aproximados y corresponden a los datos demostrativos de NutriCompra. No sustituyen orientación profesional.</p></CardContent>
          </Card>
        </div>
      </div>
        </div>
      </main>
    </div>
  )
}
