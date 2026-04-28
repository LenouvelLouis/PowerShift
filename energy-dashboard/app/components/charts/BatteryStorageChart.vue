<template>
  <div class="bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 p-5">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider">
        Battery Storage
      </h2>
      <span class="text-xs text-gray-500">MW &amp; MWh</span>
    </div>
    <BaseChart
      :option="chartOption"
      height="h-72"
      title="Battery Storage"
    />
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'

const props = defineProps<{ result: SimulationResult, startDate?: string | null }>()
const { lineOption } = useEChartsTheme()
const { buildLabels, axisLabelFormatter, tooltipLabelFormatter } = useTimeLabels(() => props.startDate)

const storageUnitsT = computed(() => props.result.result_json?.storage_units_t ?? {})

const firstUnit = computed(() => {
  const entries = Object.values(storageUnitsT.value)
  return entries[0] ?? null
})

const timeLabels = computed(() => buildLabels(firstUnit.value?.p?.length ?? 0))

const chartOption = computed(() => {
  const series: { name: string, data: number[], color: string }[] = []

  for (const [name, data] of Object.entries(storageUnitsT.value)) {
    series.push({
      name: `${name} (power)`,
      data: data.p,
      color: '#FBBF24'
    })
    if (data.state_of_charge?.length) {
      series.push({
        name: `${name} (SoC)`,
        data: data.state_of_charge,
        color: '#F97316'
      })
    }
  }

  return lineOption({
    labels: timeLabels.value,
    series,
    yTitle: 'MW / MWh',
    axisLabelFormatter,
    tooltipLabelFormatter
  })
})
</script>
