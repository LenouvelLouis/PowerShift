<template>
  <div class="bg-[#0F172A] rounded-xl border border-[#1E293B] p-5">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-sm font-semibold text-white uppercase tracking-wider">
        Supply vs Demand
      </h2>
      <span class="text-xs text-gray-500">MW / hour</span>
    </div>
    <BaseLineChart
      :data="chartData"
      :options="chartOptions"
      height="h-64"
    />
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'

const props = defineProps<{ result: SimulationResult }>()
const { lineChartOptions } = useChartTheme()

const generatorsT = computed(() => props.result.result_json?.generators_t ?? {})
const loadsT = computed(() => props.result.result_json?.loads_t ?? {})
const timeLabels = computed(() => {
  const n = Object.values(generatorsT.value)[0]?.p?.length ?? 0
  return Array.from({ length: n }, (_, i) => `H${i}`)
})

const chartData = computed(() => {
  const hours = timeLabels.value.length
  const supplyPerHour = Array.from({ length: hours }, (_, i) =>
    Object.values(generatorsT.value).reduce((sum, gen) => sum + ((gen as { p: number[] }).p[i] ?? 0), 0)
  )
  const demandPerHour = Array.from({ length: hours }, (_, i) =>
    Object.values(loadsT.value).reduce((sum, load) => sum + ((load as { p: number[] }).p[i] ?? 0), 0)
  )
  return {
    labels: timeLabels.value,
    datasets: [
      {
        label: 'Total Supply',
        data: supplyPerHour.map(v => +v.toFixed(3)),
        borderColor: '#10B981',
        backgroundColor: '#10B98118',
        fill: true,
        tension: 0.4,
        pointRadius: timeLabels.value.length > 48 ? 0 : 2,
        borderWidth: 2
      },
      {
        label: 'Total Demand',
        data: demandPerHour.map(v => +v.toFixed(3)),
        borderColor: '#EF4444',
        backgroundColor: '#EF444418',
        fill: true,
        tension: 0.4,
        pointRadius: timeLabels.value.length > 48 ? 0 : 2,
        borderWidth: 2
      }
    ]
  }
})

const chartOptions = lineChartOptions({ yTitle: 'MW', xMaxTicks: 24 })
</script>
