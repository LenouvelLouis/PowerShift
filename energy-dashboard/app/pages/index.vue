<template>
  <div class="flex flex-col min-h-full bg-gray-50 dark:bg-slate-950 p-6 gap-6">
    <!-- Backend unavailable banner -->
    <div
      v-if="referential.backendAvailable === false"
      role="alert"
      class="px-4 py-3 bg-amber-900/30 border border-amber-600/60 rounded-lg text-amber-400 text-sm flex items-center gap-2"
    >
      <span>⚠</span>
      <span>{{ $t('results.backendUnavailable') }}</span>
    </div>

    <ScenarioBar
      @loading-change="loadingScenario = $event"
      @open-compare="showCompareModal = true"
    />

    <CompareModal
      :open="showCompareModal"
      @update:open="showCompareModal = $event"
      @compare="onCompare"
    />

    <!-- Comparison view -->
    <ScenarioComparison
      v-if="compareA && compareB"
      :scenario-a="compareA"
      :scenario-b="compareB"
      @close="clearComparison"
    />

    <!-- Loading skeletons -->
    <UiShimmerSkeleton
      v-if="loadingScenario"
      :headline="$t('results.preparingScenario')"
      :subtitle="$t('results.restoringKpis')"
    />
    <UiShimmerSkeleton
      v-else-if="sim.isLiveRunning || sim.isRunning"
      :headline="$t('results.optimisingPowerFlow')"
      :subtitle="$t('results.runningLopf')"
      :badge="sim.elapsedSeconds > 0 ? `Running... ${sim.elapsedSeconds}s` : undefined"
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
        <div
          role="tablist"
          aria-label="Simulation result views"
          class="flex gap-1 border-b border-gray-200 dark:border-slate-800 mb-6"
        >
          <button
            v-for="tab in tabs"
            :id="`tab-${tab.key}`"
            :key="tab.key"
            role="tab"
            :aria-selected="activeTab === tab.key"
            :aria-controls="`tabpanel-${tab.key}`"
            class="px-4 py-2 text-sm font-medium transition-colors focus:ring-2 focus:ring-blue-500 focus:outline-none rounded-t"
            :class="activeTab === tab.key
              ? 'text-gray-900 dark:text-white border-b-2 border-blue-500 -mb-px'
              : 'text-gray-500 dark:text-gray-300 hover:text-gray-700 dark:hover:text-gray-200'"
            @click="activeTab = tab.key"
            @keydown="handleTabKeydown($event, tab.key)"
          >
            {{ tab.label }}
          </button>
        </div>

        <!-- Tab content — use v-show so NetworkCanvas stays mounted and the
             ResizeObserver can read clientWidth on the first paint -->
        <div
          v-show="activeTab === 'results'"
          id="tabpanel-results"
          role="tabpanel"
          aria-labelledby="tab-results"
          tabindex="0"
        >
          <ResultsTab :result="result" />
        </div>
        <div
          v-show="activeTab === 'graphics'"
          id="tabpanel-graphics"
          role="tabpanel"
          aria-labelledby="tab-graphics"
          tabindex="0"
        >
          <GraphicsTab :result="result" />
        </div>
        <div
          v-show="activeTab === 'network'"
          id="tabpanel-network"
          role="tabpanel"
          aria-labelledby="tab-network"
          tabindex="0"
          class="flex flex-col gap-6"
        >
          <NetworkCanvas
            :supplies="nonBatterySupplies"
            :storage="batterySupplies"
            :demands="sim.selectedDemandsWithOverrides"
            :network="sim.selectedNetworkWithOverrides"
            :result="result"
            :visible="activeTab === 'network'"
          />
          <MetricTiles :result="result" />
        </div>
      </div>
    </template>

    <!-- No result yet: show canvas with selected assets only, or empty state -->
    <template v-else>
      <NetworkCanvas
        v-if="sim.hasMinimumAssets"
        :supplies="nonBatterySupplies"
        :storage="batterySupplies"
        :demands="sim.selectedDemandsWithOverrides"
        :network="sim.selectedNetworkWithOverrides"
        :result="null"
      />
      <GuidedScenarioWizard
        v-else-if="!wizardSkipped"
        @complete="wizardSkipped = true"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'
import { useSimulationStore } from '~/stores/simulation'
import { useReferentialStore } from '~/stores/referential'
import { useHistoryStore } from '~/stores/history'

const sim = useSimulationStore()
const referential = useReferentialStore()
const history = useHistoryStore()

useSimulationUrl()

const loadingScenario = ref(false)
const wizardSkipped = ref(false)

// ─── Comparison ────────────────────────────────────────────────────────────────
const showCompareModal = ref(false)
const compareA = ref<SimulationResult | null>(null)
const compareB = ref<SimulationResult | null>(null)

function onCompare(a: SimulationResult, b: SimulationResult) {
  compareA.value = a
  compareB.value = b
}

function clearComparison() {
  compareA.value = null
  compareB.value = null
}
const result = computed(() => sim.displayedResult)

const nonBatterySupplies = computed(() =>
  sim.selectedSuppliesWithOverrides.filter(s => s.type !== 'battery_storage')
)
const batterySupplies = computed(() =>
  sim.selectedSuppliesWithOverrides.filter(s => s.type === 'battery_storage')
)

const { t } = useI18n()

const tabs = computed(() => [
  { key: 'results', label: t('results.results') },
  { key: 'graphics', label: t('results.charts') },
  { key: 'network', label: t('results.network') }
])
const activeTab = ref('results')

function handleTabKeydown(event: KeyboardEvent, _currentKey: string) {
  const keys = tabs.value.map(tab => tab.key)
  const currentIndex = keys.indexOf(activeTab.value)
  let newIndex = -1
  if (event.key === 'ArrowRight') {
    newIndex = (currentIndex + 1) % keys.length
  } else if (event.key === 'ArrowLeft') {
    newIndex = (currentIndex - 1 + keys.length) % keys.length
  } else if (event.key === 'Home') {
    newIndex = 0
  } else if (event.key === 'End') {
    newIndex = keys.length - 1
  }
  const target = keys[newIndex]
  if (newIndex >= 0 && target) {
    event.preventDefault()
    activeTab.value = target
    document.getElementById(`tab-${target}`)?.focus()
  }
}

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
    return details ?? `The power flow optimisation did not find a feasible solution for ${bad} snapshot(s). Check that generation can meet demand and that network parameters are physically consistent.`
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
