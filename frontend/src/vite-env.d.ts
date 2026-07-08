/// <reference types="vite/client" />
/// <reference types="vite-plugin-pwa/client" />

interface ImportMetaEnv {
  // Unused-by-default escape hatch for a future cross-origin build. Absolute prod API base.
  // Undefined on the web build, where requests stay same-origin via BASE_URL.
  readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
