import { configDefaults, defineConfig } from 'vitest/config'

// Tests del frontend. El backend tiene sus propios tests con Jest, por eso se
// excluye backend/ (y no se limita a una carpeta, para no ignorar tests nuevos).
export default defineConfig({
  test: {
    exclude: [...configDefaults.exclude, 'backend/**'],
    environment: 'node',
  },
})
