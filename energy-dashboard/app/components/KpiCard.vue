<template>
  <div class="bg-[#0F172A] p-6 rounded-xl border border-[#1E293B]">
    <p class="text-sm font-medium text-gray-400 mb-2">{{ label }}</p>
    <template v-if="loading">
      <div class="h-9 bg-gray-700/50 rounded-lg animate-pulse w-32 mb-1" />
      <div v-if="hasSlot" class="h-3 bg-gray-700/50 rounded-full animate-pulse mt-2" />
    </template>
    <template v-else>
      <p class="text-3xl font-bold mb-1" :class="valueClass ?? 'text-white'">{{ value }}</p>
      <slot />
    </template>
  </div>
</template>

<script setup lang="ts">
import { useSlots } from 'vue'

const props = defineProps<{
  label: string
  value?: string
  loading?: boolean
  valueClass?: string
}>()

const slots = useSlots()
const hasSlot = computed(() => !!slots.default)
</script>
