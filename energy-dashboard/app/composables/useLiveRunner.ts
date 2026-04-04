import { useDebounceFn } from '@vueuse/core'
import { previewSimulation, runSimulation, type SimulationRunRequest } from '~/composables/api'
import { useHistoryStore } from '~/stores/history'
import { useSimulationStore } from '~/stores/simulation'

/** Extract a human-readable message from any thrown error (FetchError, Error, unknown). */
function _extractErrorMessage(error: unknown): { title: string; description: string } {
  // $fetch throws a FetchError with a `data` field containing the backend JSON body
  if (error && typeof error === 'object' && 'data' in error) {
    const data = (error as { data?: unknown; status?: number }).data
    const status = (error as { status?: number }).status

    // Pydantic 422 — detail is an array of validation errors
    if (status === 422 && Array.isArray((data as { detail?: unknown })?.detail)) {
      const detail = (data as { detail: Array<{ msg: string; loc?: string[] }> }).detail
      const messages = detail.map(d => {
        const field = d.loc?.slice(1).join(' → ') ?? 'field'
        return `${field}: ${d.msg}`
      })
      return {
        title: 'Validation error (422)',
        description: messages.join('\n'),
      }
    }

    // Pydantic 422 — detail is a plain string
    if (status === 422 && typeof (data as { detail?: unknown })?.detail === 'string') {
      return {
        title: 'Validation error (422)',
        description: (data as { detail: string }).detail,
      }
    }

    // Other HTTP errors with a detail field
    if ((data as { detail?: unknown })?.detail) {
      return {
        title: `Request error (${status ?? '?'})`,
        description: String((data as { detail: unknown }).detail),
      }
    }

    // Generic HTTP error
    if (status) {
      return {
        title: `HTTP ${status}`,
        description: typeof data === 'string' ? data : JSON.stringify(data ?? {}),
      }
    }
  }

  // Standard JS Error
  if (error instanceof Error) {
    return { title: 'Preview error', description: error.message }
  }

  return { title: 'Preview error', description: 'An unknown error occurred.' }
}

/**
 * Live simulation runner.
 *
 * runPreview  — debounced (400ms), calls POST /simulation/preview (no DB write).
 *               Updates store.currentLiveResult for immediate display.
 *
 * saveSimulation — called explicitly on Save button click,
 *                  calls POST /simulation/run (writes to DB),
 *                  prepends to history, updates currentLiveResult with saved IDs.
 */
export function useLiveRunner() {
  const historyStore = useHistoryStore()
  const simStore = useSimulationStore()
  const toast = useToast()

  async function runPreview(payload: SimulationRunRequest) {
    simStore.isLiveRunning = true
    simStore.liveError = null
    try {
      const response = await previewSimulation(payload)
      simStore.currentLiveResult = response
    }
    catch (error: unknown) {
      const { title, description } = _extractErrorMessage(error)
      simStore.liveError = `${title}: ${description}`
      toast.add({
        title,
        description,
        color: 'error',
        duration: 6000,
      })
    }
    finally {
      simStore.isLiveRunning = false
    }
  }

  async function saveSimulation(payload: SimulationRunRequest) {
    simStore.isSaving = true
    try {
      const response = await runSimulation(payload)
      // Update live result with the saved response so the summary table shows real ID/timestamp
      simStore.currentLiveResult = response
      // Track this as the new reference so we can detect future changes
      simStore.setReference(response.id, payload)
      // Prepend to saved history list
      historyStore.simulationHistory.unshift({
        id: response.id,
        request_id: response.request_id,
        status: response.status,
        solver: response.solver,
        name: response.name ?? null,
        supply_ids: payload.supply_ids,
        demand_ids: payload.demand_ids,
        network_ids: payload.network_ids,
        total_supply_mwh: response.total_supply_mwh,
        total_demand_mwh: response.total_demand_mwh,
        created_at: response.created_at,
      })
      return response
    }
    finally {
      simStore.isSaving = false
    }
  }

  return {
    runPreview: useDebounceFn(runPreview, 400),
    saveSimulation,
  }
}
