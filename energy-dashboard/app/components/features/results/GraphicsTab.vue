<template>
  <div
    v-if="(result.status === 'converged' || result.status === 'optimized' || result.status === 'optimal') && hasChartData"
    class="flex flex-col gap-8 pt-4"
  >
    <!-- Production section -->
    <div>
      <p class="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-4 px-1">
        Production
      </p>
      <div class="flex flex-col gap-6">
        <ProductionChart
          :result="result"
          :start-date="startDate"
        />
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <CapacityFactorChart
            v-if="hasCapacityFactors"
            :result="result"
          />
          <PeakPowerChart
            v-if="hasChartData"
            :result="result"
          />
          <ProductionMixChart
            v-if="hasChartData"
            :result="result"
          />
        </div>
      </div>
    </div>

    <!-- Demand section -->
    <div v-if="hasConsumptionData">
      <p class="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-4 px-1">
        Demand
      </p>
      <ConsumptionChart
        :result="result"
        :start-date="startDate"
      />
    </div>

    <!-- Storage section -->
    <div v-if="hasStorageData">
      <p class="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-4 px-1">
        Storage
      </p>
      <BatteryStorageChart
        :result="result"
        :start-date="startDate"
      />
    </div>

    <!-- Bilan section -->
    <div>
      <p class="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-4 px-1">
        Bilan
      </p>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SupplyDemandChart
          :result="result"
          :start-date="startDate"
        />
        <EnergySummaryChart
          :result="result"
          height="h-64"
        />
      </div>
    </div>

    <!-- Network section (PF-specific) -->
    <div v-if="hasBusData || hasLineData">
      <p class="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-4 px-1">
        Network
      </p>
      <div class="flex flex-col gap-6">
        <BusVoltageChart
          v-if="hasBusData"
          :result="result"
          :start-date="startDate"
        />
        <LineLoadingBars
          v-if="hasLineData"
          :result="result"
        />
      </div>
    </div>
  </div>

  <div
    v-else
    class="bg-[#0F172A] rounded-xl border border-[#1E293B] p-8 flex items-center justify-center h-72 text-gray-600 text-sm mt-4"
  >
    {{ result.status === 'error' ? 'No power flow data — simulation error' : result.status === 'non_converged' ? 'Power flow did not converge' : 'No time-series data available' }}
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'

const props = defineProps<{ result: SimulationResult }>()
const startDate = computed(() => props.result.start_date || null)

const generatorsT = computed(() => props.result.result_json?.generators_t ?? {})
const loadsT = computed(() => props.result.result_json?.loads_t ?? {})
const hasChartData = computed(() => Object.keys(generatorsT.value).length > 0)
const hasConsumptionData = computed(() => Object.keys(loadsT.value).length > 0)
const hasCapacityFactors = computed(() => Object.keys(props.result.result_json?.capacity_factors ?? {}).length > 0)
const hasStorageData = computed(() => Object.keys(props.result.result_json?.storage_units_t ?? {}).length > 0)
const hasBusData = computed(() => Object.keys(props.result.result_json?.buses_t ?? {}).length > 0)
const hasLineData = computed(() => Object.keys(props.result.result_json?.lines_t ?? {}).length > 0)
</script>
