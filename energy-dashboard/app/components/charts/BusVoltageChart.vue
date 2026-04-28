<template>
  <div class="bg-[#0F172A] rounded-xl border border-[#1E293B] p-5">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-sm font-semibold text-white uppercase tracking-wider">
        Bus Voltages
      </h2>
      <span class="text-xs text-gray-500">pu</span>
    </div>
    <BaseChart
      :option="chartOption"
      height="h-48"
      title="Bus Voltages"
    />
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'

const props = defineProps<{ result: SimulationResult, startDate?: string | null }>()
const { lineOption } = useEChartsTheme()
const { buildLabels, axisLabelFormatter, tooltipLabelFormatter } = useTimeLabels(() => props.startDate)

const busesT = computed(() => props.result.result_json?.buses_t ?? {})
const timeLabels = computed(() => buildLabels(Object.values(busesT.value)[0]?.v_mag_pu?.length ?? 0))

const chartOption = computed(() =>
  lineOption({
    labels: timeLabels.value,
    series: Object.entries(busesT.value).map(([bus, data], i) => ({
      name: bus,
      data: (data as { v_mag_pu: number[] }).v_mag_pu,
      color: PALETTE[i % PALETTE.length] as string
    })),
    yTitle: 'pu',
    axisLabelFormatter,
    tooltipLabelFormatter
  })
)
</script>
