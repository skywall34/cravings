import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  base: '/cravings/',
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      devOptions: { enabled: false },
      manifest: {
        name: 'Cravings',
        short_name: 'Cravings',
        display: 'standalone',
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
