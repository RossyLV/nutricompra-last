'use client'

import { useEffect, useState } from 'react'
import { getCatalogFoods } from '@/services/data-service'
import type { CatalogFood } from '@/types'

export type CatalogFoodsState =
  | { status: 'loading' }
  | { status: 'error' }
  | { status: 'ready'; foods: CatalogFood[] }

/**
 * Carga una vez el catálogo de alimentos TPCA y expone su estado para que la
 * pantalla muestre la carga, el error o la lista sin conocer el origen.
 */
export function useCatalogFoods(): CatalogFoodsState {
  const [state, setState] = useState<CatalogFoodsState>({ status: 'loading' })

  useEffect(() => {
    let active = true
    getCatalogFoods()
      .then((foods) => {
        if (active) setState({ status: 'ready', foods })
      })
      .catch((error: unknown) => {
        // La pantalla solo muestra un mensaje genérico; el detalle va a la consola.
        console.error('No se pudo cargar el catálogo de alimentos:', error)
        if (active) setState({ status: 'error' })
      })
    return () => {
      active = false
    }
  }, [])

  return state
}
