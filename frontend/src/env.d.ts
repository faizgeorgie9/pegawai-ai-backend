/// <reference types="vite/client" />

// One flag only: dev builds made with `npm run dev:mock` answer the new endpoints from src/mock-api.ts.
// Production builds never read .env.mock, and the flag is replaced at compile time so the mock is dropped.
interface ImportMetaEnv {
  readonly VITE_MOCK_API?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
