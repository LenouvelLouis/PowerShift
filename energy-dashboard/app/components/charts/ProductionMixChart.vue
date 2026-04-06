<template>
  <div class="bg-[#0F172A] rounded-xl border border-[#1E293B] p-5">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-sm font-semibold text-white uppercase tracking-wider">
        Production Mix
      </h2>
      <span class="text-xs text-gray-500">MWh stacked</span>
    </div>
    <BaseBarChart
      :data="chartData"
      :options="chartOptions"
    />
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'

const props = defineProps<{ result: SimulationResult }>()
const { barChartOptions } = useChartTheme()

const generatorsT = computed(() => props.result.result_json?.generators_t ?? {})

const chartData = computed(() => ({
  labels: ['Production Mix'],
  datasets: Object.entries(generatorsT.value).map(([name, data], i) => {
    const total = (data as { p: number[] }).p.reduce((a, b) => a + b, 0)
    const color = generatorColor(name, i)
    return {
      label: name,
      data: [+total.toFixed(2)],
      backgroundColor: color + 'CC',
      borderColor: color,
      borderWidth: 1,
      borderRadius: 4
    }
  })
}))

const chartOptions = barChartOptions({ yTitle: 'MWh', stacked: true, showLegend: true, tooltipSuffix: ' MWh' })
</script>
