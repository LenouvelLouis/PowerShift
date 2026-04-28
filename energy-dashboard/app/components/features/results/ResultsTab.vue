<template>
  <div class="flex flex-col gap-6 pt-4">
    <!-- Data sources banner -->
    <div class="flex flex-wrap items-start gap-3 rounded-xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-4 py-3">
      <div class="flex items-center gap-1.5 text-gray-600 dark:text-gray-300">
        <UIcon
          name="i-heroicons-information-circle"
          class="w-4 h-4 shrink-0"
        />
        <span class="text-xs font-semibold uppercase tracking-wider">{{ $t('results.dataSources') }}</span>
      </div>
      <div class="flex flex-wrap gap-2 text-[11px]">
        <span class="inline-flex items-center gap-1 rounded-full bg-blue-500/10 border border-blue-500/20 px-2.5 py-0.5 text-blue-300">
          Weather: KNMI station Groningen-Eelde (06280)
        </span>
        <span class="inline-flex items-center gap-1 rounded-full bg-amber-500/10 border border-amber-500/20 px-2.5 py-0.5 text-amber-300">
          Solar profiles: Open-Meteo GHI irradiance
        </span>
        <span class="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 text-emerald-300">
          Wind profiles: KNMI 10-min measurements
        </span>
        <span class="inline-flex items-center gap-1 rounded-full bg-violet-500/10 border border-violet-500/20 px-2.5 py-0.5 text-violet-300">
          Optimization: LOPF via PyPSA + HiGHS solver
        </span>
      </div>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-2 gap-6 items-start">
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
        <template v-if="(result.status === 'converged' || result.status === 'optimized' || result.status === 'optimal') && hasChartData">
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
          class="bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 p-8 flex items-center justify-center h-72 text-gray-600 dark:text-gray-300 text-sm"
        >
          {{ result.status === 'error' ? $t('results.noDataError') : result.status === 'non_converged' ? $t('results.noConvergence') : $t('results.noTimeSeriesData') }}
        </div>
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
