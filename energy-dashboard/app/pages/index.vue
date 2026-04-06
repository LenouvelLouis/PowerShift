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
      headline="Optimising your scenario"
      subtitle="Running the simulation, results coming shortly..."
    />

    <template v-else-if="result">
      <ErrorBanner
        v-if="result.status === 'error' || result.status === 'infeasible'"
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

const sim = useSimulationStore()
const referential = useReferentialStore()

const loadingScenario = ref(false)
const result = computed(() => sim.displayedResult)

const errorHeadline = computed(() => {
  const status = result.value?.status
  if (status !== 'error' && status !== 'infeasible') return 'Simulation error'
  if (status === 'infeasible') return 'Simulation infaisable'
  if (result.value?.result_json?.error_type === 'solver_error') return 'Solver unavailable'
  return 'Simulation error'
})

const errorDescription = computed(() => {
  const status = result.value?.status
  if (status !== 'error' && status !== 'infeasible') return ''
  const details = result.value?.result_json?.error
  if (status === 'infeasible') {
    return details ?? 'L\'optimisation PyPSA n\'a pas trouvé de solution avec les assets sélectionnés. Vérifiez que la capacité de production couvre la demande.'
  }
  if (result.value?.result_json?.error_type === 'solver_error') {
    const solver = result.value.result_json?.solver ?? 'selected solver'
    return details
      ? `The solver '${solver}' is unavailable or misconfigured. ${details}`
      : `The solver '${solver}' is unavailable or misconfigured on the backend.`
  }
  return details ?? 'The optimization failed. Ensure production can cover demand and try again.'
})
</script>

<style scoped>
@keyframes shimmer {
  100% { transform: translateX(100%); }
}
</style>
