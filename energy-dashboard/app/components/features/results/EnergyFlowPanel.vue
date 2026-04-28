<template>
  <div class="bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 p-5">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider">
        {{ $t('results.energyFlow') }}
      </h3>
      <UTooltip :text="$t('results.energyFlowTooltip')">
        <UIcon
          name="i-heroicons-information-circle"
          class="w-4 h-4 text-gray-600 cursor-help"
        />
      </UTooltip>
    </div>

    <div class="space-y-1.5 text-sm">
      <!-- Local production -->
      <div class="flex items-center gap-3">
        <div class="w-3 h-3 rounded-full bg-emerald-400 shrink-0" />
        <span class="text-gray-600 dark:text-gray-400 flex-1">{{ $t('results.localProduction') }}</span>
        <span class="font-mono text-emerald-400 text-right">{{ fmt(result.total_supply_mwh) }} MWh</span>
      </div>

      <!-- Per-generator breakdown -->
      <div
        v-for="(gen, name) in generators"
        :key="name"
        class="flex items-center gap-3 pl-6"
      >
        <div
          class="w-1.5 h-1.5 rounded-full shrink-0"
          :style="{ backgroundColor: genColor(name as string) }"
        />
        <span class="text-gray-600 flex-1 text-xs truncate">{{ name }}</span>
        <span class="font-mono text-gray-500 text-xs">{{ fmt(genMwh(name as string)) }} MWh</span>
      </div>

      <!-- Battery discharge (only if > 0) -->
      <div
        v-if="batteryDischarge > 0.1"
        class="flex items-center gap-3"
      >
        <div class="w-3 h-3 rounded-full bg-yellow-400 shrink-0" />
        <span class="text-gray-600 dark:text-gray-400 flex-1">{{ $t('results.batteryDischarge') }}</span>
        <span class="font-mono text-yellow-400">+{{ fmt(batteryDischarge) }} MWh</span>
      </div>

      <!-- Grid import (only if > 0) -->
      <div
        v-if="gridImport > 0.1"
        class="flex items-center gap-3"
      >
        <div class="w-3 h-3 rounded-full bg-blue-400 shrink-0" />
        <span class="text-gray-600 dark:text-gray-400 flex-1">{{ $t('results.gridImport') }}</span>
        <span class="font-mono text-blue-400">+{{ fmt(gridImport) }} MWh</span>
      </div>

      <!-- Divider: total available -->
      <div class="border-t border-gray-200 dark:border-slate-800 my-2 pt-2 flex items-center gap-3">
        <div class="w-3 h-3 rounded-full bg-slate-500 shrink-0" />
        <span class="text-gray-700 dark:text-gray-300 flex-1 font-medium">{{ $t('results.totalAvailable') }}</span>
        <span class="font-mono text-gray-900 dark:text-white">{{ fmt(totalAvailable) }} MWh</span>
      </div>

      <!-- Consumption -->
      <div class="flex items-center gap-3">
        <div class="w-3 h-3 rounded-full bg-red-400 shrink-0" />
        <span class="text-gray-600 dark:text-gray-400 flex-1">{{ $t('results.consumptionLoads') }}</span>
        <span class="font-mono text-red-400">&minus;{{ fmt(result.total_demand_mwh) }} MWh</span>
      </div>

      <!-- Battery charge (only if > 0) -->
      <div
        v-if="batteryCharge > 0.1"
        class="flex items-center gap-3"
      >
        <div class="w-3 h-3 rounded-full bg-amber-500 shrink-0" />
        <span class="text-gray-600 dark:text-gray-400 flex-1">{{ $t('results.batteryCharge') }}</span>
        <span class="font-mono text-amber-500">&minus;{{ fmt(batteryCharge) }} MWh</span>
      </div>

      <!-- Curtailed / grid export (only if > 0) -->
      <div
        v-if="gridExport > 0.1"
        class="flex items-center gap-3"
      >
        <div class="w-3 h-3 rounded-full bg-violet-400 shrink-0" />
        <span class="text-gray-600 dark:text-gray-400 flex-1">{{ $t('results.curtailedExcess') }}</span>
        <span class="font-mono text-violet-400">&minus;{{ fmt(gridExport) }} MWh</span>
      </div>

      <!-- Balance -->
      <div class="border-t border-gray-200 dark:border-slate-800 mt-2 pt-2 flex items-center gap-3">
        <UIcon
          name="i-heroicons-scale"
          class="w-3.5 h-3.5 shrink-0"
          :class="balanceColor"
        />
        <span class="text-gray-600 dark:text-gray-400 flex-1">{{ $t('results.balance') }}</span>
        <span
          class="font-mono"
          :class="balanceColor"
        >
          {{ balance >= 0 ? '+' : '' }}{{ fmt(balance) }} MWh
        </span>
      </div>

      <!-- Curtailment warning -->
      <div
        v-if="curtailmentRatio > 0.3"
        class="mt-2 flex items-start gap-2 rounded-lg bg-amber-500/10 border border-amber-500/20 px-3 py-2"
      >
        <UIcon
          name="i-heroicons-exclamation-triangle"
          class="w-4 h-4 text-amber-400 shrink-0 mt-0.5"
        />
        <p class="text-[11px] text-amber-300 leading-relaxed">
          <strong>{{ $t('results.curtailmentWarning', { percent: (curtailmentRatio * 100).toFixed(0) }) }}</strong>
          {{ $t('results.curtailmentAdvice') }}
        </p>
      </div>

      <!-- Merit order / dispatch priority -->
      <div class="mt-2 flex items-start gap-2 rounded-lg bg-slate-500/10 border border-slate-500/20 px-3 py-2">
        <UIcon
          name="i-heroicons-queue-list"
          class="w-4 h-4 text-slate-400 shrink-0 mt-0.5"
        />
        <p class="text-[11px] text-slate-300 leading-relaxed">
          <strong>{{ $t('results.dispatchPriority') }}</strong>
          {{ $t('results.dispatchOrder') }}
        </p>
      </div>

      <!-- Balance explanation -->
      <p class="text-[11px] text-gray-600 leading-relaxed pt-1">
        <template v-if="result.status === 'optimized' || result.status === 'optimal'">
          <template v-if="Math.abs(balance) < 2">
            {{ $t('results.lopfBalanced') }}
          </template>
          <template v-else-if="gridImport > 0.1">
            {{ $t('results.gridImportExplanation', { amount: fmt(gridImport) }) }}
          </template>
          <template v-else>
            {{ $t('results.lopfOptimised', { amount: fmt(Math.abs(balance)) }) }}
          </template>
        </template>
        <template v-else-if="Math.abs(balance) < 1">
          {{ $t('results.productionMatched') }}
        </template>
        <template v-else-if="balance > 0">
          {{ $t('results.surplusExplanation', { amount: fmt(balance) }) }}
        </template>
        <template v-else>
          {{ $t('results.deficitExplanation', { amount: fmt(Math.abs(balance)) }) }}
        </template>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'

const props = defineProps<{ result: SimulationResult }>()

const fmt = (v: number | null | undefined) => v == null ? '—' : Math.abs(v) >= 1000 ? (v / 1000).toFixed(2) + 'k' : v.toFixed(1)

const generators = computed(() => props.result.result_json?.generators_t ?? {})
const storageUnits = computed(() => props.result.result_json?.storage_units_t ?? {})
const gridImport = computed(() => props.result.result_json?.grid_exchange?.total_import_mwh ?? 0)
const gridExport = computed(() => props.result.result_json?.grid_exchange?.total_export_mwh ?? 0)
const balance = computed(() => props.result.balance_mwh ?? 0)

const batteryDischarge = computed(() =>
  Object.values(storageUnits.value).reduce((sum, su) =>
    sum + su.p.reduce((a: number, v: number) => a + Math.max(0, v), 0), 0
  )
)
const batteryCharge = computed(() =>
  Object.values(storageUnits.value).reduce((sum, su) =>
    sum + su.p.reduce((a: number, v: number) => a + Math.max(0, -v), 0), 0
  )
)

const totalAvailable = computed(() =>
  (props.result.total_supply_mwh ?? 0) + batteryDischarge.value + gridImport.value
)

const curtailmentRatio = computed(() => {
  const localProd = props.result.total_supply_mwh ?? 0
  const curtailed = gridExport.value
  const totalRenewable = localProd + curtailed
  return totalRenewable > 0 ? curtailed / totalRenewable : 0
})

function genMwh(name: string): number {
  const ts = generators.value[name]
  if (!ts?.p) return 0
  return ts.p.reduce((a: number, v: number) => a + v, 0)
}

const COLORS = ['#34d399', '#60a5fa', '#f59e0b', '#a78bfa', '#f87171', '#2dd4bf', '#fb923c']
function genColor(name: string): string {
  const keys = Object.keys(generators.value)
  return COLORS[keys.indexOf(name) % COLORS.length] ?? '#94a3b8'
}

const balanceColor = computed(() => {
  const b = balance.value
  if (props.result.status === 'error') return 'text-gray-500'
  if (Math.abs(b) < 2) return 'text-emerald-400'
  return b > 0 ? 'text-blue-400' : 'text-amber-400'
})
</script>
