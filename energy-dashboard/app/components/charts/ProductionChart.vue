<template>
  <div class="bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 p-5">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider">
        {{ $t('charts.productionByGenerator') }}
      </h2>
      <span class="text-xs text-gray-500">MW / hour</span>
    </div>
    <BaseChart
      :option="chartOption"
      height="h-72"
      :title="$t('charts.productionByGenerator')"
    />
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'

const props = defineProps<{ result: SimulationResult, startDate?: string | null }>()
const { lineOption } = useEChartsTheme()
const { buildLabels, axisLabelFormatter, tooltipLabelFormatter } = useTimeLabels(() => props.startDate)

const generatorsT = computed(() => props.result.result_json?.generators_t ?? {})
const timeLabels = computed(() => buildLabels(Object.values(generatorsT.value)[0]?.p?.length ?? 0))

const chartOption = computed(() =>
  lineOption({
    labels: timeLabels.value,
    series: Object.entries(generatorsT.value).map(([name, data], i) => ({
      name,
      data: (data as { p: number[] }).p.map(v => (Object.is(v, -0) ? 0 : v)),
      color: generatorColor(name, i)
    })),
    yTitle: 'MW',
    axisLabelFormatter,
    tooltipLabelFormatter
  })
)
</script>
