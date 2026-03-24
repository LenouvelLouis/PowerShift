// https://nuxt.com/docs/api/configuration/nuxt-config
import Aura from '@primeuix/themes/aura'
export default defineNuxtConfig({
  modules: [
    '@nuxt/eslint',
    '@nuxt/ui',
    '@pinia/nuxt',
    '@vueuse/nuxt',
    '@nuxt/icon'
  ],

  // ← AJOUTE ce bloc pour corriger les icons
  icon: {
    collections: [
      'heroicons',
      'lucide'
    ],
    // @ts-ignore do not delete or Vs code will consider it as an error
    provider: 'unjs'
  },

  devtools: { enabled: true },

  css: ['~/assets/css/main.css'],

  routeRules: {
    '/': { prerender: true }
  },

  // Proxy géré par server/routes/api/[...path].ts (runtime, pas build-time)

  compatibilityDate: '2025-01-15',

  // ← Ajoute ce bloc pour Pinia persistedstate
  pinia: {
    storesDirs: ['./app/stores/**'],
  },

  eslint: {
    config: {
      stylistic: {
        commaDangle: 'never',
        braceStyle: '1tbs'
      }
    }
  }
})