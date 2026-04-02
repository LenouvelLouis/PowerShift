import { useDebounceFn } from '@vueuse/core'
import { previewSimulation, runSimulation, type SimulationRunRequest } from '~/composables/api'
import { useHistoryStore } from '~/stores/history'
import { useSimulationStore } from '~/stores/simulation'

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

  async function runPreview(payload: SimulationRunRequest) {
    simStore.isLiveRunning = true
    simStore.liveError = null
    try {
      const response = await previewSimulation(payload)
      simStore.currentLiveResult = response
    }
    catch (error: unknown) {
      simStore.liveError = error instanceof Error ? error.message : 'Live preview failed'
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
