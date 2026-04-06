<template>
  <div class="bg-[#0F172A] rounded-xl border border-[#1E293B] p-5">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-sm font-semibold text-white uppercase tracking-wider">
        Consumption by Load
      </h2>
      <span class="text-xs text-gray-500">MW / hour</span>
    </div>
    <BaseChart :option="chartOption" height="h-72" />
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'

const props = defineProps<{ result: SimulationResult }>()
const { lineOption } = useEChartsTheme()

const loadsT = computed(() => props.result.result_json?.loads_t ?? {})
const timeLabels = computed(() => {
  const n = Object.values(loadsT.value)[0]?.p?.length ?? 0
  return Array.from({ length: n }, (_, i) => `H${i}`)
})

const chartOption = computed(() =>
  lineOption({
    labels: timeLabels.value,
    series: Object.entries(loadsT.value).map(([name, data], i) => ({
      name,
      data: (data as { p: number[] }).p,
      color: PALETTE[(i + 4) % PALETTE.length] as string
    })),
    yTitle: 'MW'
  })
)
</script>
