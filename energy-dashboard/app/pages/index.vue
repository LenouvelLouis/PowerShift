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
      <ErrorBanner
        v-if="result.status === 'error' || result.status === 'non_converged'"
        :headline="errorHeadline"
        :description="errorDescription"
      />
      <KpiCardsGrid :result="result" />
      <UTabs
        :items="[{ label: 'Results', slot: 'results' }, { label: 'Graphics', slot: 'charts' }]"
        class="w-full"
      >
        <template #results>
          <ResultsTab :result="result" />
        </template>
        <template #charts>
          <GraphicsTab :result="result" />
        </template>
      </UTabs>
    </template>

    <EmptyState v-else />
  </div>
</template>

<script setup lang="ts">
import { useSimulationStore } from '~/stores/simulation'
import { useReferentialStore } from '~/stores/referential'
import { useHistoryStore } from '~/stores/history'

const sim = useSimulationStore()
const referential = useReferentialStore()
const history = useHistoryStore()

useSimulationUrl()

const loadingScenario = ref(false)
const result = computed(() => sim.displayedResult)

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
    const bad = conv?.non_converged_snapshots?.length ?? 0
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
    // non-critical — page still usable
  }
})
</script>

<style scoped>
@keyframes shimmer {
  100% { transform: translateX(100%); }
}
</style>
