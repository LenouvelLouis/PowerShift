<template>
  <div class="bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 p-5">
    <h3 class="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
      {{ $t('results.simulationSummary') }}
    </h3>
    <div class="space-y-2.5 text-sm">
      <div class="flex justify-between items-center">
        <span class="text-gray-600 dark:text-gray-400">ID</span>
        <span class="font-mono text-gray-700 dark:text-gray-300 text-xs">{{ result.id.slice(-8) }}</span>
      </div>
      <div class="flex justify-between items-center">
        <span class="text-gray-600 dark:text-gray-400">{{ $t('results.status') }}</span>
        <span
          class="font-semibold"
          :class="(result.status === 'converged' || result.status === 'optimized' || result.status === 'optimal') ? 'text-emerald-400' : 'text-red-400'"
        >
          {{ statusLabel }}
        </span>
      </div>
      <div class="flex justify-between items-center">
        <span class="text-gray-600 dark:text-gray-400">{{ $t('results.supply') }}</span>
        <span class="text-gray-900 dark:text-white font-mono">{{ result.status === 'error' ? '—' : `${fmt(result.total_supply_mwh)} MWh` }}</span>
      </div>
      <div class="flex justify-between items-center">
        <span class="text-gray-600 dark:text-gray-400">{{ $t('results.demand') }}</span>
        <span class="text-gray-900 dark:text-white font-mono">{{ result.status === 'error' ? '—' : `${fmt(result.total_demand_mwh)} MWh` }}</span>
      </div>
      <div class="flex justify-between items-center">
        <span class="text-gray-600 dark:text-gray-400">{{ $t('results.balance') }}</span>
        <span
          class="font-mono"
          :class="balanceColor"
        >{{ result.status === 'error' ? '—' : `${fmt(result.balance_mwh)} MWh` }}</span>
      </div>
      <template v-if="convergence">
        <div class="flex justify-between items-center">
          <span class="text-gray-600 dark:text-gray-400">{{ $t('results.convergence') }}</span>
          <span
            class="font-mono text-xs"
            :class="convergence.all_converged ? 'text-emerald-400' : 'text-amber-400'"
          >
            {{ convergence.converged_count }}/{{ convergence.total_snapshots }} {{ $t('results.snapshots') }}
          </span>
        </div>
      </template>
      <template v-if="gridExchange">
        <div class="flex justify-between items-center">
          <span class="text-gray-600 dark:text-gray-400">{{ $t('results.gridImportLabel') }}</span>
          <span class="font-mono text-blue-400">{{ fmt(gridExchange.total_import_mwh) }} MWh</span>
        </div>
        <div class="flex justify-between items-center">
          <span class="text-gray-600 dark:text-gray-400">{{ $t('results.curtailed') }}</span>
          <span class="font-mono text-violet-400">{{ fmt(gridExchange.total_export_mwh) }} MWh</span>
        </div>
      </template>
      <div class="flex justify-between items-center border-t border-gray-200 dark:border-slate-800 pt-2.5 mt-1">
        <span class="text-gray-600 dark:text-gray-400">{{ $t('results.created') }}</span>
        <span class="font-mono text-gray-700 dark:text-gray-300 text-xs">{{ new Date(result.created_at).toLocaleString() }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'

const props = defineProps<{ result: SimulationResult }>()

const { t } = useI18n()

const fmt = (v: number | null | undefined) => v == null ? '—' : v.toFixed(2)

const statusLabel = computed(() => {
  const s = props.result.status
  if (s === 'optimized' || s === 'optimal') return t('results.optimised')
  if (s === 'converged') return t('results.converged')
  if (s === 'non_converged') return t('results.nonConverged')
  if (s === 'infeasible') return t('results.infeasible')
  return t('results.error')
})

const balanceColor = computed(() => {
  const b = props.result.balance_mwh ?? 0
  if (props.result.status === 'error') return 'text-gray-500'
  if (Math.abs(b) < 0.001) return 'text-emerald-400'
  return b > 0 ? 'text-blue-400' : 'text-red-400'
})

const convergence = computed(() => props.result.result_json?.convergence ?? null)
const gridExchange = computed(() => props.result.result_json?.grid_exchange ?? null)
</script>
