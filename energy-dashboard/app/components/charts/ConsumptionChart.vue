<template>
  <div class="bg-[#0F172A] rounded-xl border border-[#1E293B] p-5">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-sm font-semibold text-white uppercase tracking-wider">
        Consumption by Load
      </h2>
      <span class="text-xs text-gray-500">MW / hour</span>
    </div>
    <BaseChart :option="chartOption" height="h-72" title="Consumption by Load" />
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'

const props = defineProps<{ result: SimulationResult; startDate?: string | null }>()
const { lineOption } = useEChartsTheme()
const { buildLabels, axisLabelFormatter, tooltipLabelFormatter } = useTimeLabels(() => props.startDate)

const loadsT = computed(() => props.result.result_json?.loads_t ?? {})
const timeLabels = computed(() => buildLabels(Object.values(loadsT.value)[0]?.p?.length ?? 0))

const chartOption = computed(() =>
  lineOption({
    labels: timeLabels.value,
    series: Object.entries(loadsT.value).map(([name, data], i) => ({
      name,
      data: (data as { p: number[] }).p,
      color: PALETTE[(i + 4) % PALETTE.length] as string
    })),
    yTitle: 'MW',
    axisLabelFormatter,
    tooltipLabelFormatter
  })
)
</script>
