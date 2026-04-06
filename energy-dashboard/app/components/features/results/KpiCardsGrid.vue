<template>
  <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
    <KpiCard label="Status">
      <span
        class="text-xl font-bold"
        :class="result.status === 'optimal' ? 'text-emerald-400' : 'text-red-400'"
      >
        {{ result.status === 'optimal' ? 'Optimal' : 'Infeasible' }}
      </span>
    </KpiCard>
    <KpiCard
      label="Power Balance"
      :value="result.status === 'error' ? '—' : fmt(result.balance_mwh)"
      :value-class="balanceColor"
    >
      <p class="text-xs text-gray-500 mt-1">
        MWh
      </p>
    </KpiCard>
    <KpiCard
      label="Total Supply"
      :value="result.status === 'error' ? '—' : fmt(result.total_supply_mwh)"
    >
      <p class="text-xs text-gray-500 mt-1">
        MWh
      </p>
    </KpiCard>
    <KpiCard
      label="Total Demand"
      :value="result.status === 'error' ? '—' : fmt(result.total_demand_mwh)"
    >
      <p class="text-xs text-gray-500 mt-1">
        MWh
      </p>
    </KpiCard>
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
</script>
