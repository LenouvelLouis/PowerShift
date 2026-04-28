<template>
  <div class="bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 p-5">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider">
        {{ $t('charts.productionMix') }}
      </h2>
      <span class="text-xs text-gray-500">MWh stacked</span>
    </div>
    <BaseChart
      :option="chartOption"
      :title="$t('charts.productionMix')"
    />
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'

const props = defineProps<{ result: SimulationResult }>()
const { t } = useI18n()
const { barOption } = useEChartsTheme()

const generatorsT = computed(() => props.result.result_json?.generators_t ?? {})

const chartOption = computed(() =>
  barOption({
    labels: [t('charts.productionMix')],
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
