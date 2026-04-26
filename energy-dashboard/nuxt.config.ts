// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  modules: [
    '@nuxt/eslint',
    '@nuxt/ui',
    '@pinia/nuxt',
    '@vueuse/nuxt',
    '@nuxt/icon'
  ],

  components: {
    dirs: [
      { path: '~/components/ui', prefix: 'Ui' },
      { path: '~/components/features/sidebar', prefix: 'Sidebar' },
      { path: '~/components', pathPrefix: false }
    ]
  },

  icon: {
    collections: [
      'heroicons',
      'lucide'
    ],
    // @ts-expect-error do not delete or VS Code will consider it as an error
    provider: 'unjs'
  },

  devtools: { enabled: true },

  css: ['~/assets/css/main.css'],

  routeRules: {
    '/': { prerender: true }
  },

  compatibilityDate: '2025-01-15',

  pinia: {
    storesDirs: ['./app/stores/**']
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
