<template>
  <div class="bg-[#0F172A] rounded-xl border border-[#1E293B] p-5">
    <h3 class="text-sm font-semibold text-white uppercase tracking-wider mb-4">
      Line Loading (peak)
    </h3>
    <div class="space-y-3">
      <div
        v-for="{ name, loading, color } in lineLoadings"
        :key="name"
      >
        <div class="flex items-center justify-between mb-1">
          <span
            class="text-xs text-gray-400 truncate mr-2 flex items-center gap-1"
            :title="name"
          >
            <UIcon
              name="i-heroicons-link"
              class="w-3 h-3 shrink-0"
            />
            {{ name }}
          </span>
          <span
            class="font-mono text-xs shrink-0"
            :class="loading > 100 ? 'text-red-400' : loading > 80 ? 'text-amber-400' : 'text-white'"
          >
            {{ loading.toFixed(1) }}%
          </span>
        </div>
        <div class="w-full bg-[#1E293B] rounded-full h-1.5">
          <div
            class="h-1.5 rounded-full transition-all duration-700"
            :style="{ width: `${Math.min(loading, 100)}%`, backgroundColor: color }"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'

const props = defineProps<{ result: SimulationResult }>()

const lineLoadings = computed(() => {
  const lt = props.result.result_json?.lines_t ?? {}
  return Object.entries(lt)
    .map(([name, data]) => {
      const loadings = (data as { loading: number[] }).loading ?? []
      const peak = loadings.length ? Math.max(...loadings) : 0
      const color = peak > 100 ? '#EF4444' : peak > 80 ? '#F59E0B' : '#10B981'
      return { name, loading: peak, color }
    })
    .filter(l => l.loading > 0)
})
</script>
