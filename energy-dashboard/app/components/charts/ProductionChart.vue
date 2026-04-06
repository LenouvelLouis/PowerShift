<template>
  <div class="bg-[#0F172A] rounded-xl border border-[#1E293B] p-5">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-sm font-semibold text-white uppercase tracking-wider">
        Production by Generator
      </h2>
      <span class="text-xs text-gray-500">MW / hour</span>
    </div>
    <BaseChart :option="chartOption" height="h-72" />
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'

const props = defineProps<{ result: SimulationResult }>()
const { lineOption } = useEChartsTheme()

const generatorsT = computed(() => props.result.result_json?.generators_t ?? {})
const timeLabels = computed(() => {
  const n = Object.values(generatorsT.value)[0]?.p?.length ?? 0
  return Array.from({ length: n }, (_, i) => `H${i}`)
})

const chartOption = computed(() =>
  lineOption({
    labels: timeLabels.value,
    series: Object.entries(generatorsT.value).map(([name, data], i) => ({
      name,
      data: (data as { p: number[] }).p,
      color: generatorColor(name, i)
    })),
    yTitle: 'MW'
  })
)
</script>
