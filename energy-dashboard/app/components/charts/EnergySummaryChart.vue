<template>
  <div class="bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 p-5">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider">
        Energy Summary
      </h2>
      <span class="text-xs text-gray-500">MWh</span>
    </div>
    <BaseChart
      :option="chartOption"
      :height="height"
      title="Energy Summary"
    />
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'

const props = defineProps<{ result: SimulationResult, height?: string }>()
const { barOption } = useEChartsTheme()

const generatorsT = computed(() => props.result.result_json?.generators_t ?? {})
const loadsT = computed(() => props.result.result_json?.loads_t ?? {})

const chartOption = computed(() => {
  const supplyLabels = Object.keys(generatorsT.value)
  const demandLabels = Object.keys(loadsT.value)
  const labels = [...supplyLabels, ...demandLabels]
  const supplyTotals = supplyLabels.map(name => (generatorsT.value[name] as { p: number[] }).p.reduce((a, b) => a + b, 0))
  const demandTotals = demandLabels.map(name => (loadsT.value[name] as { p: number[] }).p.reduce((a, b) => a + b, 0))
  const colors = [
    ...supplyLabels.map((name, i) => generatorColor(name, i)),
    ...demandLabels.map(() => '#EF4444')
  ]
  return barOption({
    labels,
    series: [{ name: 'Total Energy (MWh)', data: [...supplyTotals, ...demandTotals], colors }],
    yTitle: 'MWh',
    tooltipSuffix: ' MWh'
  })
})
</script>
