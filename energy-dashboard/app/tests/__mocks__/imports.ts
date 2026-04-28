/**
 * Mock for Nuxt auto-imports (#imports).
 * Re-exports Vue reactivity primitives so stores work outside Nuxt context.
 */
export { ref, computed, watch, reactive, toRef, toRefs, nextTick } from 'vue'
