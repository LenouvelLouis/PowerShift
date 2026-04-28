<template>
  <div class="bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 p-5">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider">
        Capacity Factors
      </h2>
      <span class="text-xs text-gray-500">%</span>
    </div>
    <BaseChart
      :option="chartOption"
      title="Capacity Factors"
    />
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'

const props = defineProps<{ result: SimulationResult }>()
const { barOption } = useEChartsTheme()

const capacityFactors = computed(() => {
  const cf = props.result.result_json?.capacity_factors ?? {}
  return Object.entries(cf).map(([name, value], i) => ({
    name,
    cf: value as number,
    color: generatorColor(name, i)
  }))
})

const chartOption = computed(() =>
  barOption({
    labels: capacityFactors.value.map(d => d.name),
    series: [{
      name: 'Capacity Factor (%)',
      data: capacityFactors.value.map(d => +(d.cf * 100).toFixed(1)),
      colors: capacityFactors.value.map(d => d.color)
    }],
    yTitle: '%',
    yMax: 100,
    tooltipSuffix: ' %'
  })
)
</script>
