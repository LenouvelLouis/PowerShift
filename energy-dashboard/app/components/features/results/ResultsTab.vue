<template>
  <div class="grid grid-cols-1 xl:grid-cols-2 gap-6 items-start pt-4">
    <!-- LEFT: energy flow + summary table + capacity factors + energy bar -->
    <div class="flex flex-col gap-6">
      <EnergyFlowPanel :result="result" />
      <SimulationSummary :result="result" />
      <CapacityFactorBars
        v-if="capacityFactors.length"
        :factors="capacityFactors"
      />
      <EnergySummaryChart
        v-if="hasChartData"
        :result="result"
        height="h-52"
      />
    </div>

    <!-- RIGHT: production + consumption + storage line charts -->
    <div class="flex flex-col gap-6">
      <template v-if="(result.status === 'converged' || result.status === 'optimized') && hasChartData">
        <ProductionChart :result="result" />
        <ConsumptionChart
          v-if="hasConsumptionData"
          :result="result"
        />
        <BatteryStorageChart
          v-if="hasStorageData"
          :result="result"
        />
      </template>
      <div
        v-else
        class="bg-[#0F172A] rounded-xl border border-[#1E293B] p-8 flex items-center justify-center h-72 text-gray-600 text-sm"
      >
        {{ result.status === 'error' ? 'No power flow data — simulation error' : result.status === 'non_converged' ? 'Power flow did not converge' : 'No time-series data available' }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'

const props = defineProps<{ result: SimulationResult }>()

const generatorsT = computed(() => props.result.result_json?.generators_t ?? {})
const loadsT = computed(() => props.result.result_json?.loads_t ?? {})
const hasChartData = computed(() => Object.keys(generatorsT.value).length > 0)
const hasConsumptionData = computed(() => Object.keys(loadsT.value).length > 0)
const storageUnitsT = computed(() => props.result.result_json?.storage_units_t ?? {})
const hasStorageData = computed(() => Object.keys(storageUnitsT.value).length > 0)

const capacityFactors = computed(() => {
  const cf = props.result.result_json?.capacity_factors ?? {}
  return Object.entries(cf).map(([name, value], i) => ({
    name,
    cf: value as number,
    color: generatorColor(name, i)
  }))
})
</script>
