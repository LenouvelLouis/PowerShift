<template>
  <header class="bg-[#0F172A] border-b border-[#1E293B] shrink-0">
    <SaveChoiceModal
      :open="showSaveChoiceModal"
      :loading="store.isSaving"
      @update:open="showSaveChoiceModal = $event"
      @replace="handleSaveReplace"
      @new="handleSaveNew"
    />
    <SolverHelpModal
      :open="showSolverHelpModal"
      @update:open="showSolverHelpModal = $event"
    />

    <HeaderRow1
      :can-save="canSave"
      :can-export="canExport"
      @toggle-sidebar="$emit('toggle-sidebar')"
      @save="handleSave"
      @export="handleExport"
    />
    <HeaderRow2
      @open-solver-help="showSolverHelpModal = true"
      @header-rename="handleHeaderRename"
    />
  </header>
</template>

<script setup lang="ts">
import { useSimulationStore } from '~/stores/simulation'
import { useReferentialStore } from '~/stores/referential'
import { useHistoryStore } from '~/stores/history'
import { useLiveRunner } from '~/composables/useLiveRunner'
import type { SimulationRunRequest } from '~/composables/api'

const emit = defineEmits<{ 'toggle-sidebar': [] }>()

const store = useSimulationStore()
const referential = useReferentialStore()
const history = useHistoryStore()
const toast = useToast()
const { runPreview, saveSimulation } = useLiveRunner()
const { handleExport } = useScenarioIO()

// ─── Computed ─────────────────────────────────────────────────────────────────

const canSave = computed(() =>
  !store.isSaving && store.hasMinimumAssets
  && !!referential.backendAvailable && !store.paramsMatchSaved
)
const canExport = computed(() => !!(history.currentResult || history.selectedSimulationId))

// ─── Live preview watcher ─────────────────────────────────────────────────────

watch(
  () => [
    store.selectedSupplyIds.join(),
    store.selectedDemandIds.join(),
    store.selectedNetworkIds.join(),
    store.snapshotHours,
    store.solver,
    store.optimizationObjective,
    store.startDate,
    store.endDate,
    JSON.stringify(store.buildPayload().asset_overrides),
  ],
  () => {
    if (store.isLoadingScenario) return
    if (!referential.backendAvailable || !store.hasMinimumAssets) return
    runPreview(store.buildPayload())
  }
)


// Warn when solar/wind assets are selected without a date range
const _noDateWarnShown = ref(false)
watch(
  () => ({ ids: store.selectedSupplyIds, start: store.startDate }),
  ({ ids: _ids, start }) => {
    if (start) { _noDateWarnShown.value = false; return }
    if (_noDateWarnShown.value) return
    const hasWeatherAsset = store.selectedSupplies.some(
      (s: { type: string }) => s.type === 'solar_panel' || s.type === 'wind_turbine'
    )
    if (!hasWeatherAsset) return
    _noDateWarnShown.value = true
    toast.add({
      title: 'No date range selected',
      description: 'Solar and wind assets will run at rated capacity (p_nom) without a real weather profile. Select a date range for realistic results.',
      color: 'warning',
      duration: 8000
    })
  },
  { deep: false }
)

// ─── Save logic ───────────────────────────────────────────────────────────────

const showSaveChoiceModal = ref(false)
const showSolverHelpModal = ref(false)

function _buildSavePayload(): SimulationRunRequest & { name?: string } {
  return { ...store.buildPayload(), name: store.scenarioName || undefined }
}

async function _doSave(payload: ReturnType<typeof _buildSavePayload>) {
  try {
    const result = await saveSimulation(payload)
    history.currentResult = result
    history.selectedSimulationId = result.id
    store.selectedHistoryId = result.id
    if (result.status === 'error') {
      const errorType = result.result_json?.error_type
      const solver = result.result_json?.solver ?? store.solver
      const backendError = result.result_json?.error
      const description = errorType === 'solver_error'
        ? `Solver '${solver}' unavailable or misconfigured.${backendError ? ` ${backendError}` : ''}`
        : `${backendError ?? 'PyPSA did not find an optimal solution.'} (solver: ${solver})`
      toast.add({
        title: errorType === 'solver_error' ? 'Solver execution error' : 'Simulation failed',
        description,
        color: 'error'
      })
    } else {
      toast.add({ title: 'Simulation saved', description: `Status: ${result.status}`, color: 'success' })
      for (const msg of result.result_json?.warnings ?? []) {
        toast.add({ title: 'Weather data warning', description: msg, color: 'warning', duration: 8000 })
      }
    }
  } catch {
    toast.add({ title: 'Save error', description: store.error ?? 'Failed to save simulation', color: 'error' })
  }
}

function handleSave() {
  if (!referential.backendAvailable) {
    toast.add({ title: 'Backend unavailable', description: 'Start the API server first', color: 'warning' })
    return
  }
  if (!store.hasMinimumAssets) {
    toast.add({ title: 'Incomplete selection', description: 'Select at least one supply and one demand', color: 'warning' })
    return
  }
  if (store.referenceSimId !== null) {
    showSaveChoiceModal.value = true
    return
  }
  _doSave(_buildSavePayload())
}

async function handleSaveReplace() {
  showSaveChoiceModal.value = false
  try {
    await history.deleteEntry(store.referenceSimId!)
  } catch { /* already deleted — proceed */ }
  await _doSave(_buildSavePayload())
}

function _generateCopyName(baseName: string): string {
  const existingNames = new Set(history.simulationHistory.map((s: { name?: string | null }) => s.name))
  const candidate = `${baseName} (copy)`
  if (!existingNames.has(candidate)) return candidate
  let i = 2
  while (existingNames.has(`${baseName} (#${i})`)) i++
  return `${baseName} (#${i})`
}

async function handleSaveNew() {
  showSaveChoiceModal.value = false
  const payload = _buildSavePayload()
  if (payload.name) {
    payload.name = _generateCopyName(payload.name)
    store.scenarioName = payload.name
  }
  await _doSave(payload)
}

async function handleHeaderRename() {
  const id = history.selectedSimulationId
  const name = store.scenarioName.trim()
  if (!id || !name) return
  try {
    await history.renameEntry(id, name)
    toast.add({ title: 'Scenario renamed', color: 'success' })
  } catch {
    toast.add({ title: 'Rename failed', color: 'error' })
  }
}
</script>
