<template>
  <div class="flex flex-col gap-6">
    <!-- ── 6 KPI tiles ──────────────────────────────────────────────────── -->
    <div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
      <!-- Balance -->
      <div class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-4 flex flex-col gap-1.5">
        <div class="flex items-center gap-1.5 text-gray-500">
          <UIcon
            name="i-heroicons-scale"
            class="w-4 h-4"
          />
          <span class="text-[11px] uppercase tracking-wider font-semibold">Balance</span>
        </div>
        <p
          class="text-2xl font-bold font-mono"
          :class="balanceColor"
        >
          {{ fmt(result.balance_mwh) }}
        </p>
        <p class="text-[11px] text-gray-600">
          MWh
        </p>
      </div>

      <!-- Supply -->
      <div class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-4 flex flex-col gap-1.5">
        <div class="flex items-center gap-1.5 text-emerald-500">
          <UIcon
            name="i-heroicons-bolt"
            class="w-4 h-4"
          />
          <span class="text-[11px] uppercase tracking-wider font-semibold">Supply</span>
        </div>
        <p class="text-2xl font-bold font-mono text-emerald-400">
          {{ fmt(result.total_supply_mwh) }}
        </p>
        <p class="text-[11px] text-gray-600">
          MWh
        </p>
      </div>

      <!-- Demand -->
      <div class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-4 flex flex-col gap-1.5">
        <div class="flex items-center gap-1.5 text-red-500">
          <UIcon
            name="i-heroicons-home"
            class="w-4 h-4"
          />
          <span class="text-[11px] uppercase tracking-wider font-semibold">Demand</span>
        </div>
        <p class="text-2xl font-bold font-mono text-red-400">
          {{ fmt(result.total_demand_mwh) }}
        </p>
        <p class="text-[11px] text-gray-600">
          MWh
        </p>
      </div>

      <!-- Grid Import -->
      <div class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-4 flex flex-col gap-1.5">
        <div class="flex items-center gap-1.5 text-blue-500">
          <UIcon
            name="i-heroicons-arrow-down-tray"
            class="w-4 h-4"
          />
          <span class="text-[11px] uppercase tracking-wider font-semibold">Import</span>
        </div>
        <p class="text-2xl font-bold font-mono text-blue-400">
          {{ gridExchange ? fmt(gridExchange.total_import_mwh) : '—' }}
        </p>
        <p class="text-[11px] text-gray-600">
          MWh
        </p>
      </div>

      <!-- Grid Export -->
      <div class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-4 flex flex-col gap-1.5">
        <div class="flex items-center gap-1.5 text-amber-500">
          <UIcon
            name="i-heroicons-arrow-up-tray"
            class="w-4 h-4"
          />
          <span class="text-[11px] uppercase tracking-wider font-semibold">Export</span>
        </div>
        <p class="text-2xl font-bold font-mono text-amber-400">
          {{ gridExchange ? fmt(gridExchange.total_export_mwh) : '—' }}
        </p>
        <p class="text-[11px] text-gray-600">
          MWh
        </p>
      </div>

      <!-- Convergence -->
      <div class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-4 flex flex-col gap-1.5">
        <div
          class="flex items-center gap-1.5"
          :class="convergence?.all_converged ? 'text-emerald-500' : 'text-amber-500'"
        >
          <UIcon
            :name="convergence?.all_converged ? 'i-heroicons-check-circle' : 'i-heroicons-exclamation-triangle'"
            class="w-4 h-4"
          />
          <span class="text-[11px] uppercase tracking-wider font-semibold">Convergence</span>
        </div>
        <p
          class="text-2xl font-bold font-mono"
          :class="convergence?.all_converged ? 'text-emerald-400' : 'text-amber-400'"
        >
          {{ convergence ? `${convergence.converged_count}/${convergence.total_snapshots}` : '—' }}
        </p>
        <p class="text-[11px] text-gray-600">
          snapshots
        </p>
      </div>
    </div>

    <!-- ── Bottom row: capacity factors + simulation summary ────────────── -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Capacity factors -->
      <div
        v-if="capacityFactors.length"
        class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-5"
      >
        <h3 class="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider mb-4">
          Capacity Factors
        </h3>
        <div class="space-y-3">
          <div
            v-for="{ name, cf, color } in capacityFactors"
            :key="name"
          >
            <div class="flex items-center justify-between mb-1.5">
              <div class="flex items-center gap-1.5">
                <UIcon
                  :name="generatorIcon(name)"
                  class="w-3 h-3 text-gray-500 shrink-0"
                />
                <span
                  class="text-xs text-gray-600 dark:text-gray-400 truncate max-w-[160px]"
                  :title="name"
                >{{ name }}</span>
              </div>
              <span class="text-xs font-mono text-gray-900 dark:text-white shrink-0 ml-2">{{ (cf * 100).toFixed(1) }}%</span>
            </div>
            <div class="w-full bg-gray-200 dark:bg-slate-800 rounded-full h-2">
              <div
                class="h-2 rounded-full transition-all duration-700"
                :style="{ width: `${Math.min(cf * 100, 100)}%`, backgroundColor: color }"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Simulation summary -->
      <div class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-5">
        <h3 class="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider mb-4">
          Simulation Summary
        </h3>
        <div class="space-y-2.5 text-sm">
          <div class="flex justify-between items-center">
            <span class="text-gray-600 dark:text-gray-500">Status</span>
            <span
              class="font-semibold"
              :class="(result.status === 'converged' || result.status === 'optimized' || result.status === 'optimal') ? 'text-emerald-400' : 'text-red-400'"
            >
              {{ (result.status === 'optimized' || result.status === 'optimal') ? 'Optimised' : result.status === 'converged' ? 'Converged' : result.status === 'non_converged' ? 'Non-converged' : result.status === 'infeasible' ? 'Infeasible' : 'Error' }}
            </span>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-gray-600 dark:text-gray-500">ID</span>
            <span class="font-mono text-gray-600 dark:text-gray-400 text-xs">{{ result.id.slice(-8) }}</span>
          </div>
          <div
            v-if="result.name"
            class="flex justify-between items-center"
          >
            <span class="text-gray-600 dark:text-gray-500">Name</span>
            <span class="text-gray-700 dark:text-gray-300 text-xs truncate max-w-40">{{ result.name }}</span>
          </div>
          <div
            v-if="violations?.overloads?.length"
            class="flex justify-between items-center"
          >
            <span class="text-gray-600 dark:text-gray-500">Overloaded lines</span>
            <span class="text-red-400 font-mono text-xs">{{ violations.overloads.length }}</span>
          </div>
          <div
            v-if="violations?.overvoltages?.length"
            class="flex justify-between items-center"
          >
            <span class="text-gray-600 dark:text-gray-500">Overvoltage buses</span>
            <span class="text-amber-400 font-mono text-xs">{{ violations.overvoltages.length }}</span>
          </div>
          <div class="flex justify-between items-center border-t border-gray-200 dark:border-slate-800 pt-2.5 mt-1">
            <span class="text-gray-600 dark:text-gray-500">Created</span>
            <span class="font-mono text-gray-600 dark:text-gray-400 text-xs">{{ new Date(result.created_at).toLocaleString() }}</span>
          </div>
        </div>
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
const violations = computed(() => props.result.result_json?.violations ?? null)

const capacityFactors = computed(() => {
  const cf = props.result.result_json?.capacity_factors ?? {}
  return Object.entries(cf).map(([name, value], i) => ({
    name,
    cf: value as number,
    color: generatorColor(name, i)
  }))
})
</script>
