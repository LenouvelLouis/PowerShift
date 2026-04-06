<template>
  <div class="bg-[#0F172A] rounded-xl border border-[#1E293B] p-5">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-sm font-semibold text-white uppercase tracking-wider">
        Consumption by Load
      </h2>
      <span class="text-xs text-gray-500">MW / hour</span>
    </div>
    <BaseLineChart
      :data="chartData"
      :options="chartOptions"
      height="h-72"
    />
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'

const props = defineProps<{ result: SimulationResult }>()
const { lineChartOptions } = useChartTheme()

const loadsT = computed(() => props.result.result_json?.loads_t ?? {})
const timeLabels = computed(() => {
  const n = Object.values(loadsT.value)[0]?.p?.length ?? 0
  return Array.from({ length: n }, (_, i) => `H${i}`)
})

const chartData = computed(() => ({
  labels: timeLabels.value,
  datasets: Object.entries(loadsT.value).map(([name, data], i) => ({
    label: name,
    data: (data as { p: number[] }).p,
    borderColor: PALETTE[(i + 4) % PALETTE.length],
    backgroundColor: PALETTE[(i + 4) % PALETTE.length] + '26',
    fill: false,
    tension: 0.4,
    pointRadius: timeLabels.value.length > 48 ? 0 : 2,
    pointHoverRadius: 5,
    borderWidth: 2
  }))
}))

const chartOptions = lineChartOptions({ yTitle: 'MW', xMaxTicks: 24 })
</script>
