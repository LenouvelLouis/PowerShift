import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import { resolve } from 'node:path'

export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      imports: ['vue'],
      dts: false
    })
  ],
  resolve: {
    alias: {
      '~': resolve(__dirname, 'app'),
      '#imports': resolve(__dirname, 'app/tests/__mocks__/imports.ts')
    }
  },
  test: {
    environment: 'happy-dom',
    globals: true,
    root: '.',
    include: ['app/tests/**/*.test.ts']
  }
})
