<template>
  <div class="bg-[#0F172A] rounded-xl border border-[#1E293B] p-5">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-sm font-semibold text-white uppercase tracking-wider">
        {{ chartTitle }}
      </h2>
      <span class="text-xs text-gray-500">{{ chartUnit }}</span>
    </div>
    <BaseChart
      :option="chartOption"
      height="h-48"
      :title="chartTitle"
    />
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'

const props = defineProps<{ result: SimulationResult, startDate?: string | null }>()
const { lineOption } = useEChartsTheme()
const { buildLabels, axisLabelFormatter, tooltipLabelFormatter } = useTimeLabels(() => props.startDate)

const busesT = computed(() => props.result.result_json?.buses_t ?? {})

// Detect which data field is available: v_mag_pu (power flow) or marginal_price (OPF)
const dataField = computed(() => {
  const firstBus = Object.values(busesT.value)[0]
  if (!firstBus) return 'v_mag_pu'
  if (firstBus.marginal_price) return 'marginal_price'
  if (firstBus.v_mag_pu) return 'v_mag_pu'
  return 'v_mag_pu'
})

const chartTitle = computed(() => dataField.value === 'marginal_price' ? 'Bus Marginal Prices' : 'Bus Voltages')
const chartUnit = computed(() => dataField.value === 'marginal_price' ? '\u20AC/MWh' : 'pu')

const timeLabels = computed(() => {
  const firstBus = Object.values(busesT.value)[0]
  if (!firstBus) return []
  const arr = dataField.value === 'marginal_price' ? firstBus.marginal_price : firstBus.v_mag_pu
  return buildLabels(arr?.length ?? 0)
})

const chartOption = computed(() =>
  lineOption({
    labels: timeLabels.value,
    series: Object.entries(busesT.value).map(([bus, data], i) => ({
      name: bus,
      data: (dataField.value === 'marginal_price' ? data.marginal_price : data.v_mag_pu) ?? [],
      color: PALETTE[i % PALETTE.length] as string
    })),
    yTitle: chartUnit.value,
    axisLabelFormatter,
    tooltipLabelFormatter
  })
)
</script>
