import { defineConfig } from 'vite'
import { fileURLToPath } from 'node:url'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  base: '/cravings/',
  build: {
    rollupOptions: {
      input: {
        main:  fileURLToPath(new URL('./index.html', import.meta.url)),
        admin: fileURLToPath(new URL('./admin.html', import.meta.url)),
      },
    },
  },
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      devOptions: { enabled: false },
      manifest: {
        id: '/cravings/',
        name: 'Cravings',
        short_name: 'Cravings',
        description: 'Swipe to find what to eat — personalized dish recommendations and nearby restaurants.',
        display: 'standalone',
        orientation: 'portrait',
        categories: ['food'],
        start_url: '/cravings/',
        scope: '/cravings/',
        theme_color: '#FFF8F0',
        background_color: '#FFF8F0',
        icons: [
          { src: '/cravings/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
          { src: '/cravings/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
          { src: '/cravings/icon-512-maskable.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
    }),
  ],
  server: {
    proxy: {
      '/api': 'http://localhost:8080',
      '/images': 'http://localhost:8080',
    },
  },
})
