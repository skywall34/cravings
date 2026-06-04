/// <reference types="vite/client" />

interface ImportMetaEnv {
  // Set only in the Capacitor build (.env.capacitor). Absolute prod API base.
  // Undefined on the web build, where requests stay same-origin via BASE_URL.
  readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
