<template>
  <div class="bg-[#0F172A] rounded-xl border border-[#1E293B] p-5">
    <h3 class="text-sm font-semibold text-white uppercase tracking-wider mb-4">
      Simulation Summary
    </h3>
    <div class="space-y-2.5 text-sm">
      <div class="flex justify-between items-center">
        <span class="text-gray-400">ID</span>
        <span class="font-mono text-gray-300 text-xs">{{ result.id.slice(-8) }}</span>
      </div>
      <div class="flex justify-between items-center">
        <span class="text-gray-400">Status</span>
        <span
          class="font-semibold"
          :class="(result.status === 'converged' || result.status === 'optimized') ? 'text-emerald-400' : 'text-red-400'"
        >
          {{ result.status === 'optimized' ? 'Optimised' : result.status === 'converged' ? 'Converged' : result.status === 'non_converged' ? 'Non-converged' : 'Error' }}
        </span>
      </div>
      <div class="flex justify-between items-center">
        <span class="text-gray-400">Supply</span>
        <span class="text-white font-mono">{{ result.status === 'error' ? '—' : `${fmt(result.total_supply_mwh)} MWh` }}</span>
      </div>
      <div class="flex justify-between items-center">
        <span class="text-gray-400">Demand</span>
        <span class="text-white font-mono">{{ result.status === 'error' ? '—' : `${fmt(result.total_demand_mwh)} MWh` }}</span>
      </div>
      <div class="flex justify-between items-center">
        <span class="text-gray-400">Balance</span>
        <span
          class="font-mono"
          :class="balanceColor"
        >{{ result.status === 'error' ? '—' : `${fmt(result.balance_mwh)} MWh` }}</span>
      </div>
      <template v-if="convergence">
        <div class="flex justify-between items-center">
          <span class="text-gray-400">Convergence</span>
          <span
            class="font-mono text-xs"
            :class="convergence.all_converged ? 'text-emerald-400' : 'text-amber-400'"
          >
            {{ convergence.converged_count }}/{{ convergence.total_snapshots }} snapshots
          </span>
        </div>
      </template>
      <template v-if="gridExchange">
        <div class="flex justify-between items-center">
          <span class="text-gray-400">Grid Import</span>
          <span class="font-mono text-blue-400">{{ fmt(gridExchange.total_import_mwh) }} MWh</span>
        </div>
        <div class="flex justify-between items-center">
          <span class="text-gray-400">Curtailed</span>
          <span class="font-mono text-violet-400">{{ fmt(gridExchange.total_export_mwh) }} MWh</span>
        </div>
      </template>
      <div class="flex justify-between items-center border-t border-[#1E293B] pt-2.5 mt-1">
        <span class="text-gray-400">Created</span>
        <span class="font-mono text-gray-300 text-xs">{{ new Date(result.created_at).toLocaleString() }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'

const props = defineProps<{ result: SimulationResult }>()

const fmt = (v: number | null | undefined) => v == null ? '—' : v.toFixed(2)

const balanceColor = computed(() => {
  const b = props.result.balance_mwh ?? 0
  if (props.result.status === 'error') return 'text-gray-500'
  if (Math.abs(b) < 0.001) return 'text-emerald-400'
  return b > 0 ? 'text-blue-400' : 'text-red-400'
})

const convergence = computed(() => props.result.result_json?.convergence ?? null)
const gridExchange = computed(() => props.result.result_json?.grid_exchange ?? null)
</script>
