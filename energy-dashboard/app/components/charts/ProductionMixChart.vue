<template>
  <div class="bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 p-5">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider">
        Production Mix
      </h2>
      <span class="text-xs text-gray-500">MWh stacked</span>
    </div>
    <BaseChart
      :option="chartOption"
      title="Production Mix"
    />
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'

const props = defineProps<{ result: SimulationResult }>()
const { barOption } = useEChartsTheme()

const generatorsT = computed(() => props.result.result_json?.generators_t ?? {})

const chartOption = computed(() =>
  barOption({
    labels: ['Production Mix'],
    series: Object.entries(generatorsT.value).map(([name, data], i) => ({
      name,
      data: [+(data as { p: number[] }).p.reduce((a, b) => a + b, 0).toFixed(2)],
      colors: [generatorColor(name, i)]
    })),
    yTitle: 'MWh',
    stacked: true,
    showLegend: true,
    tooltipSuffix: ' MWh'
  })
)
</script>
