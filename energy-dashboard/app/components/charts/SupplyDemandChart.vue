<template>
  <div class="bg-[#0F172A] rounded-xl border border-[#1E293B] p-5">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-sm font-semibold text-white uppercase tracking-wider">
        Supply vs Demand
      </h2>
      <span class="text-xs text-gray-500">MW / hour</span>
    </div>
    <BaseChart
      :option="chartOption"
      height="h-64"
      title="Supply vs Demand"
    />
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'

const props = defineProps<{ result: SimulationResult, startDate?: string | null }>()
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
      { name: 'Total Supply', data: supplyPerHour.map(v => +v.toFixed(3)), color: '#10B981' },
      { name: 'Total Demand', data: demandPerHour.map(v => +v.toFixed(3)), color: '#EF4444' }
    ],
    yTitle: 'MW',
    axisLabelFormatter,
    tooltipLabelFormatter
  })
})
</script>
