import type { CapacitorConfig } from '@capacitor/cli'

const config: CapacitorConfig = {
  appId: 'com.themshin.cravings',
  appName: 'Cravings',
  webDir: 'dist',
  server: {
    // WebView serves bundled assets from https://localhost so requests to the
    // prod API (https://themshin.com) are not blocked as mixed content.
    androidScheme: 'https',
  },
}

export default config
