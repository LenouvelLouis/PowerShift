<template>
  <footer class="bg-[#0F172A] border-t border-[#1E293B] shrink-0 relative overflow-hidden">
    <!-- Running progress line -->
    <div
      v-if="store.isLiveRunning"
      class="absolute top-0 left-0 h-0.5 bg-amber-400/60 animate-pulse w-full"
    />

    <!-- Insufficient capacity warning -->
    <div
      v-if="supplyShortfall"
      class="flex items-center justify-center gap-2 px-4 py-1 bg-red-950/60 border-b border-red-800/50 text-red-400 text-xs font-semibold"
    >
      <UIcon name="i-heroicons-exclamation-triangle" class="w-3.5 h-3.5 shrink-0" />
      Supply capacity ({{ totalSupplyMw }} MW) is less than demand ({{ totalDemandMw }} MW) — simulation will be infeasible
    </div>

    <div class="h-10 flex items-center px-4 gap-0 text-xs">
      <!-- Status -->
      <div class="flex items-center gap-2 px-3 border-r border-[#1E293B]">
        <span class="text-gray-500 uppercase tracking-wider">Status</span>
        <span class="flex items-center gap-1">
          <span
            class="inline-block h-1.5 w-1.5 rounded-full"
            :class="kpiStatus === 'optimal' ? 'bg-emerald-400'
              : kpiStatus === 'error' ? 'bg-red-500'
                : kpiStatus === 'running' ? 'bg-amber-400 animate-pulse'
                  : 'bg-gray-600'"
          />
          <span
            class="font-semibold transition-colors duration-300"
            :class="kpiStatus === 'optimal' ? 'text-emerald-400'
              : kpiStatus === 'error' ? 'text-red-400'
                : kpiStatus === 'running' ? 'text-amber-400'
                  : 'text-gray-500'"
          >
            {{ kpiStatus === 'optimal' ? 'Optimal' : kpiStatus === 'error' ? 'Infeasible' : kpiStatus === 'running' ? 'Running…' : '—' }}
          </span>
        </span>
      </div>

      <!-- Total Supply -->
      <div class="flex items-center gap-2 px-3 border-r border-[#1E293B]">
        <span class="text-gray-500 uppercase tracking-wider">Supply</span>
        <span class="font-mono text-white transition-all duration-300">{{ kpiSupply }}</span>
        <span class="text-gray-600">MWh</span>
      </div>

      <!-- Total Demand -->
      <div class="flex items-center gap-2 px-3 border-r border-[#1E293B]">
        <span class="text-gray-500 uppercase tracking-wider">Demand</span>
        <span class="font-mono text-white transition-all duration-300">{{ kpiDemand }}</span>
        <span class="text-gray-600">MWh</span>
      </div>

      <!-- Balance -->
      <div class="flex items-center gap-2 px-3 border-r border-[#1E293B]">
        <span class="text-gray-500 uppercase tracking-wider">Balance</span>
        <span
          class="font-mono transition-all duration-300"
          :class="kpiBalanceColor"
        >{{ kpiBalance }}</span>
        <span class="text-gray-600">MWh</span>
      </div>

      <!-- Asset counts + MW -->
      <div class="flex items-center gap-3 px-3">
        <span class="text-gray-500 uppercase tracking-wider">Assets</span>
        <span class="flex items-center gap-1.5 font-mono">
          <span class="text-amber-400">{{ store.selectedSupplyIds.length }}S</span>
          <span
            class="text-[10px] font-semibold px-1 py-0.5 rounded"
            :class="supplyShortfall ? 'text-red-400 bg-red-950/60' : 'text-amber-300/70 bg-amber-950/40'"
          >{{ totalSupplyMw }} MW</span>
          <span class="text-gray-600">·</span>
          <span class="text-emerald-400">{{ store.selectedDemandIds.length }}D</span>
          <span class="text-[10px] text-emerald-300/70 bg-emerald-950/40 font-semibold px-1 py-0.5 rounded">{{ totalDemandMw }} MW</span>
          <span class="text-gray-600">·</span>
          <span class="text-blue-400">{{ store.selectedNetworkIds.length }}N</span>
          <span class="text-[10px] text-blue-300/70 bg-blue-950/40 font-semibold px-1 py-0.5 rounded">{{ totalNetworkMva }} MVA</span>
        </span>
      </div>

      <div class="flex-1" />

      <!-- Running indicator -->
      <div
        v-if="store.isLiveRunning"
        class="flex items-center gap-1.5 text-amber-400 pr-2"
      >
        <div class="animate-spin h-3 w-3 border-t border-amber-400 rounded-full" />
        <span>Optimizing…</span>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
import { useSimulationStore } from '~/stores/simulation'
import type { Supply, Demand, NetworkComponent } from '~/composables/api'

const store = useSimulationStore()

const kpiResult = computed(() => store.displayedResult)

const kpiStatus = computed(() => {
  if (store.isLiveRunning || store.isRunning) return 'running'
  return kpiResult.value?.status ?? null
})

const kpiSupply = computed(() => {
  const v = kpiResult.value?.total_supply_mwh
  return v != null ? v.toFixed(2) : '—'
})

const kpiDemand = computed(() => {
  const v = kpiResult.value?.total_demand_mwh
  return v != null ? v.toFixed(2) : '—'
})

const kpiBalance = computed(() => {
  const v = kpiResult.value?.balance_mwh
  return v != null ? v.toFixed(2) : '—'
})

const kpiBalanceColor = computed(() => {
  const v = kpiResult.value?.balance_mwh
  if (v == null || kpiResult.value?.status === 'error') return 'text-gray-500'
  if (Math.abs(v) < 0.001) return 'text-emerald-400'
  return v > 0 ? 'text-blue-400' : 'text-red-400'
})

const totalSupplyMw = computed(() =>
  (store.selectedSupplies as Supply[]).reduce((sum, s) => {
    const overrides = store.getOverrides('supply', s.id)
    return sum + (overrides.capacity_mw ?? s.capacity_mw ?? 0)
  }, 0)
)

const totalDemandMw = computed(() =>
  (store.selectedDemands as Demand[]).reduce((sum, d) => {
    const overrides = store.getOverrides('demand', d.id)
    return sum + (overrides.load_mw ?? d.load_mw ?? 0)
  }, 0)
)

const totalNetworkMva = computed(() =>
  (store.selectedNetwork as NetworkComponent[]).reduce((sum, n) => {
    const overrides = store.getOverrides('network', n.id)
    return sum + (overrides.capacity_mva ?? n.capacity_mva ?? 0)
  }, 0)
)

const supplyShortfall = computed(() =>
  store.selectedSupplyIds.length > 0
  && store.selectedDemandIds.length > 0
  && totalSupplyMw.value < totalDemandMw.value
)
</script>
