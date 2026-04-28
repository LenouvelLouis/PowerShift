<template>
  <div class="bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 p-5">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider">
        {{ $t('charts.supplyVsDemand') }}
      </h2>
      <span class="text-xs text-gray-500">MW / hour</span>
    </div>
    <BaseChart
      :option="chartOption"
      height="h-64"
      :title="$t('charts.supplyVsDemand')"
    />
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'

const props = defineProps<{ result: SimulationResult, startDate?: string | null }>()
const { t } = useI18n()
const { lineOption } = useEChartsTheme()
const { buildLabels, axisLabelFormatter, tooltipLabelFormatter } = useTimeLabels(() => props.startDate)

const generatorsT = computed(() => props.result.result_json?.generators_t ?? {})
const loadsT = computed(() => props.result.result_json?.loads_t ?? {})
const timeLabels = computed(() => buildLabels(Object.values(generatorsT.value)[0]?.p?.length ?? 0))

const chartOption = computed(() => {
  const hours = timeLabels.value.length
  const supplyPerHour = Array.from({ length: hours }, (_, i) =>
    Object.values(generatorsT.value).reduce((sum, gen) => sum + ((gen as { p: number[] }).p[i] ?? 0), 0)
  )
  const demandPerHour = Array.from({ length: hours }, (_, i) =>
    Object.values(loadsT.value).reduce((sum, load) => sum + ((load as { p: number[] }).p[i] ?? 0), 0)
  )
  return lineOption({
    labels: timeLabels.value,
    series: [
      { name: t('charts.totalSupply'), data: supplyPerHour.map(v => +v.toFixed(3)), color: '#10B981' },
      { name: t('charts.totalDemand'), data: demandPerHour.map(v => +v.toFixed(3)), color: '#EF4444' }
    ],
    yTitle: 'MW',
    axisLabelFormatter,
    tooltipLabelFormatter
  })
})
</script>
