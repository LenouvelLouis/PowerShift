<template>
  <div class="flex flex-col min-h-full bg-[#020617] p-6 gap-6">

    <!-- Backend unavailable banner -->
    <div
      v-if="referential.backendAvailable === false"
      class="px-4 py-3 bg-amber-900/30 border border-amber-600/60 rounded-lg text-amber-400 text-sm flex items-center gap-2"
    >
      <span>⚠</span>
      <span>Backend unavailable — start the API server to enable live simulations.</span>
    </div>

    <ScenarioBar @loading-change="loadingScenario = $event" />

    <!-- Loading skeletons -->
    <UiShimmerSkeleton
      v-if="loadingScenario"
      headline="Preparing your scenario"
      subtitle="Restoring KPIs, charts, and simulation context..."
    />
    <UiShimmerSkeleton
      v-else-if="sim.isLiveRunning || sim.isRunning"
      headline="Computing power flow"
      subtitle="Running AC power flow analysis, results coming shortly..."
    />

    <template v-else-if="result">
      <!-- Error / non-convergence banner -->
      <ErrorBanner
        v-if="result.status === 'error' || result.status === 'non_converged'"
        :headline="errorHeadline"
        :description="errorDescription"
      />

      <!-- Big KPI cards -->
      <KpiCardsGrid :result="result" />

      <!-- Tabs: Résultats / Graphiques / Réseau -->
      <div>
        <!-- Tab bar -->
        <div class="flex gap-1 border-b border-[#1E293B] mb-6">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            class="px-4 py-2 text-sm font-medium transition-colors"
            :class="activeTab === tab.key
              ? 'text-white border-b-2 border-blue-500 -mb-px'
              : 'text-gray-500 hover:text-gray-300'"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
          </button>
        </div>

        <!-- Tab content — use v-show so NetworkCanvas stays mounted and the
             ResizeObserver can read clientWidth on the first paint -->
        <div v-show="activeTab === 'results'">
          <ResultsTab :result="result" />
        </div>
        <div v-show="activeTab === 'graphics'">
          <GraphicsTab :result="result" />
        </div>
        <div v-show="activeTab === 'network'" class="flex flex-col gap-6">
          <NetworkCanvas
            :supplies="sim.selectedSupplies"
            :demands="sim.selectedDemands"
            :network="sim.selectedNetwork"
            :result="result"
            :visible="activeTab === 'network'"
          />
          <NetworkCanvasMetricTiles :result="result" />
        </div>
      </div>
    </template>

    <!-- No result yet: show canvas with selected assets only, or empty state -->
    <template v-else>
      <NetworkCanvas
        v-if="sim.hasMinimumAssets"
        :supplies="sim.selectedSupplies"
        :demands="sim.selectedDemands"
        :network="sim.selectedNetwork"
        :result="null"
      />
      <EmptyState v-else />
    </template>
  </div>
</template>

<script setup lang="ts">
import { useSimulationStore } from '~/stores/simulation'
import { useReferentialStore } from '~/stores/referential'
import { useHistoryStore } from '~/stores/history'

const sim        = useSimulationStore()
const referential = useReferentialStore()
const history    = useHistoryStore()

useSimulationUrl()

const loadingScenario = ref(false)
const result = computed(() => sim.displayedResult)

const tabs = [
  { key: 'results',  label: 'Results' },
  { key: 'graphics', label: 'Charts' },
  { key: 'network',  label: 'Network' },
]
const activeTab = ref('results')

const errorHeadline = computed(() => {
  const status = result.value?.status
  if (status !== 'error' && status !== 'non_converged') return 'Simulation error'
  if (status === 'non_converged') return 'Power flow did not converge'
  if (result.value?.result_json?.error_type === 'convergence_error') return 'Convergence error'
  return 'Simulation error'
})

const errorDescription = computed(() => {
  const status = result.value?.status
  if (status !== 'error' && status !== 'non_converged') return ''
  const details = result.value?.result_json?.error
  if (status === 'non_converged') {
    const conv = result.value?.result_json?.convergence
    const bad  = conv?.non_converged_snapshots?.length ?? 0
    return details ?? `The AC power flow did not converge for ${bad} snapshot(s). Check that generation can meet demand and that network parameters are physically consistent.`
  }
  if (result.value?.result_json?.error_type === 'convergence_error') {
    return details ?? 'The power flow solver failed to converge. Ensure network parameters are valid.'
  }
  return details ?? 'The power flow simulation failed. Check asset configurations and try again.'
})

onMounted(async () => {
  try {
    await referential.loadReferential()
    if (referential.backendAvailable) {
      await history.loadHistory()
    }
  } catch {
    // non-critical
  }
})
</script>

<style scoped>
@keyframes shimmer {
  100% { transform: translateX(100%); }
}
</style>
