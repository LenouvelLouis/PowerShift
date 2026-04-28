<template>
  <div class="bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 p-5">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider">
        {{ $t('charts.peakPower') }}
      </h2>
      <span class="text-xs text-gray-500">MW max</span>
    </div>
    <BaseChart
      :option="chartOption"
      :title="$t('charts.peakPower')"
    />
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'

const props = defineProps<{ result: SimulationResult }>()
const { t } = useI18n()
const { barOption } = useEChartsTheme()

const generatorsT = computed(() => props.result.result_json?.generators_t ?? {})

const chartOption = computed(() => {
  const labels = Object.keys(generatorsT.value)
  const data = labels.map(name => +Math.max(...(generatorsT.value[name] as { p: number[] }).p).toFixed(2))
  const colors = labels.map((name, i) => generatorColor(name, i))
  return barOption({
    labels,
    series: [{ name: t('charts.peakPowerMw'), data, colors }],
    yTitle: 'MW',
    tooltipSuffix: ' MW'
  })
})
</script>
