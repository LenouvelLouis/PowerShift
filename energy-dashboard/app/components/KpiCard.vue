<template>
  <div class="bg-white dark:bg-slate-900 p-6 rounded-xl border border-gray-200 dark:border-slate-800">
    <p class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
      {{ label }}
    </p>
    <template v-if="loading">
      <div class="h-9 bg-gray-700/50 rounded-lg animate-pulse w-32 mb-1" />
      <div
        v-if="hasSlot"
        class="h-3 bg-gray-700/50 rounded-full animate-pulse mt-2"
      />
    </template>
    <template v-else>
      <p
        class="text-3xl font-bold mb-1"
        :class="valueClass ?? 'text-gray-900 dark:text-white'"
      >
        {{ value }}
      </p>
      <slot />
    </template>
  </div>
</template>

<script setup lang="ts">
import { useSlots } from 'vue'

const _props = defineProps<{
  label: string
  value?: string
  loading?: boolean
  valueClass?: string
}>()

const slots = useSlots()
const hasSlot = computed(() => !!slots.default)
</script>
