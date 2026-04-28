<template>
  <div
    role="region"
    aria-label="Key performance indicators"
    class="grid grid-cols-2 lg:grid-cols-4 gap-4"
  >
    <!-- Status -->
    <div
      :aria-label="`${$t('results.status')}: ${statusLabel}`"
      class="rounded-2xl border p-5 flex flex-col gap-2"
      :class="isSuccess
        ? 'bg-emerald-950/30 border-emerald-800/40'
        : result.status === 'error'
          ? 'bg-red-950/30 border-red-800/40'
          : 'bg-amber-950/30 border-amber-800/40'"
    >
      <div class="flex items-center gap-2">
        <UIcon
          :name="isSuccess ? 'i-heroicons-check-circle' : 'i-heroicons-exclamation-circle'"
          class="w-6 h-6"
          :class="isSuccess ? 'text-emerald-400' : result.status === 'error' ? 'text-red-400' : 'text-amber-400'"
        />
        <span class="text-xs font-semibold uppercase tracking-wider text-gray-600 dark:text-gray-400">{{ $t('results.status') }}</span>
      </div>
      <p
        class="text-2xl font-bold"
        :class="isSuccess ? 'text-emerald-400' : result.status === 'error' ? 'text-red-400' : 'text-amber-400'"
      >
        {{ statusLabel }}
      </p>
    </div>

    <!-- Balance -->
    <div
      :aria-label="`Balance: ${result.status === 'error' ? 'unavailable' : fmtShort(result.balance_mwh) + ' MWh'}`"
      class="rounded-2xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 flex flex-col gap-2"
    >
      <div class="flex items-center gap-2 text-gray-600 dark:text-gray-400">
        <UIcon
          name="i-heroicons-scale"
          class="w-6 h-6"
        />
        <span class="text-xs font-semibold uppercase tracking-wider">{{ $t('results.balance') }}</span>
      </div>
      <p
        class="text-3xl font-bold font-mono"
        :class="balanceColor"
      >
        {{ result.status === 'error' ? '—' : fmtShort(result.balance_mwh) }}
      </p>
      <p class="text-xs text-gray-600 dark:text-gray-400">
        MWh
      </p>
    </div>

    <!-- Supply -->
    <div
      :aria-label="`Supply: ${result.status === 'error' ? 'unavailable' : fmtShort(result.total_supply_mwh) + ' MWh'}`"
      class="rounded-2xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 flex flex-col gap-2"
    >
      <div class="flex items-center gap-2 text-emerald-500">
        <UIcon
          name="i-heroicons-bolt"
          class="w-6 h-6"
        />
        <span class="text-xs font-semibold uppercase tracking-wider text-gray-600 dark:text-gray-400">{{ $t('results.supply') }}</span>
        <UTooltip text="MWh = MW × hours. A 100 MW plant running 24h produces 2,400 MWh.">
          <UIcon
            name="i-heroicons-question-mark-circle"
            class="w-3.5 h-3.5 text-gray-600 dark:text-gray-400 cursor-help shrink-0"
          />
        </UTooltip>
      </div>
      <p class="text-3xl font-bold font-mono text-emerald-400">
        {{ result.status === 'error' ? '—' : fmtShort(result.total_supply_mwh) }}
      </p>
      <p class="text-xs text-gray-600 dark:text-gray-400">
        MWh
      </p>
    </div>

    <!-- Demand -->
    <div
      :aria-label="`Demand: ${result.status === 'error' ? 'unavailable' : fmtShort(result.total_demand_mwh) + ' MWh'}`"
      class="rounded-2xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 flex flex-col gap-2"
    >
      <div class="flex items-center gap-2 text-red-500">
        <UIcon
          name="i-heroicons-home"
          class="w-6 h-6"
        />
        <span class="text-xs font-semibold uppercase tracking-wider text-gray-600 dark:text-gray-400">{{ $t('results.demand') }}</span>
        <UTooltip text="MWh = MW × hours. A 100 MW plant running 24h produces 2,400 MWh.">
          <UIcon
            name="i-heroicons-question-mark-circle"
            class="w-3.5 h-3.5 text-gray-600 dark:text-gray-400 cursor-help shrink-0"
          />
        </UTooltip>
      </div>
      <p class="text-3xl font-bold font-mono text-red-400">
        {{ result.status === 'error' ? '—' : fmtShort(result.total_demand_mwh) }}
      </p>
      <p class="text-xs text-gray-600 dark:text-gray-400">
        MWh
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'

const props = defineProps<{ result: SimulationResult }>()

const { t } = useI18n()

function fmtShort(v: number | null | undefined): string {
  if (v == null) return '—'
  if (Math.abs(v) >= 1000) return (v / 1000).toFixed(1) + 'k'
  return v.toFixed(1)
}

const isSuccess = computed(() =>
  props.result.status === 'converged' || props.result.status === 'optimized' || props.result.status === 'optimal'
)
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
</script>
