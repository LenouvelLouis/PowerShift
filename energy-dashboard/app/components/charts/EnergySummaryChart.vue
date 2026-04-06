<template>
  <div class="bg-[#0F172A] rounded-xl border border-[#1E293B] p-5">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-sm font-semibold text-white uppercase tracking-wider">
        Energy Summary
      </h2>
      <span class="text-xs text-gray-500">MWh</span>
    </div>
    <BaseBarChart
      :data="chartData"
      :options="chartOptions"
      :height="height"
    />
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'

const props = defineProps<{ result: SimulationResult, height?: string }>()
const { barChartOptions } = useChartTheme()

const generatorsT = computed(() => props.result.result_json?.generators_t ?? {})
const loadsT = computed(() => props.result.result_json?.loads_t ?? {})

const chartData = computed(() => {
  const supplyLabels = Object.keys(generatorsT.value)
  const demandLabels = Object.keys(loadsT.value)
  const labels = [...supplyLabels, ...demandLabels]
  const supplyTotals = supplyLabels.map(name => (generatorsT.value[name] as { p: number[] }).p.reduce((a, b) => a + b, 0))
  const demandTotals = demandLabels.map(name => (loadsT.value[name] as { p: number[] }).p.reduce((a, b) => a + b, 0))
  const colors = labels.map((name, i) => demandLabels.includes(name) ? '#EF4444' : generatorColor(name, i))
  return {
    labels,
    datasets: [{
      label: 'Total Energy (MWh)',
      data: [...supplyTotals, ...demandTotals],
      backgroundColor: colors.map(c => c + 'CC'),
      borderColor: colors,
      borderWidth: 1,
      borderRadius: 4
    }]
  }
})

const chartOptions = barChartOptions({ yTitle: 'MWh', tooltipSuffix: ' MWh' })
</script>
