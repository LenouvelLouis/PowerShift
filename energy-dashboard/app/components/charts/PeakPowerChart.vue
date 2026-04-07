<template>
  <div class="bg-[#0F172A] rounded-xl border border-[#1E293B] p-5">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-sm font-semibold text-white uppercase tracking-wider">
        Peak Power
      </h2>
      <span class="text-xs text-gray-500">MW max</span>
    </div>
    <BaseChart :option="chartOption" title="Peak Power" />
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'

const props = defineProps<{ result: SimulationResult }>()
const { barOption } = useEChartsTheme()

const generatorsT = computed(() => props.result.result_json?.generators_t ?? {})

const chartOption = computed(() => {
  const labels = Object.keys(generatorsT.value)
  const data = labels.map(name => +Math.max(...(generatorsT.value[name] as { p: number[] }).p).toFixed(2))
  const colors = labels.map((name, i) => generatorColor(name, i))
  return barOption({
    labels,
    series: [{ name: 'Peak Power (MW)', data, colors }],
    yTitle: 'MW',
    tooltipSuffix: ' MW'
  })
})
</script>
