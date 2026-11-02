import { defineConfig } from 'vitest/config'

// Tests de la lógica del frontend (lib/). El backend tiene sus propios tests
// con Jest, por eso Vitest solo busca dentro de lib/.
export default defineConfig({
  test: {
    include: ['lib/**/*.test.ts'],
    environment: 'node',
  },
})
