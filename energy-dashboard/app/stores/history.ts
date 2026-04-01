import { defineStore } from 'pinia'
import {
  fetchSimulations,
  fetchSimulationById,
  deleteSimulation,
  renameSimulation,
  type SimulationResult,
  type SimulationListItem,
} from '~/composables/api'

export const useHistoryStore = defineStore('history', () => {
  // ─── État ────────────────────────────────────────────────────────────────────
  const simulationHistory = ref<SimulationListItem[]>([])
  const currentResult = ref<SimulationResult | null>(null)
  const selectedSimulationId = ref<string | null>(null)

  // ─── Actions ─────────────────────────────────────────────────────────────────

  async function loadHistory() {
    try {
      simulationHistory.value = await fetchSimulations()
    }
    catch {
      // silently fail — history is non-critical
    }
  }

  async function loadSimulationById(id: string) {
    const result = await fetchSimulationById(id)
    currentResult.value = result
    selectedSimulationId.value = id
  }

  async function deleteEntry(id: string) {
    await deleteSimulation(id)
    simulationHistory.value = simulationHistory.value.filter(s => s.id !== id)
    if (currentResult.value?.id === id) currentResult.value = null
    if (selectedSimulationId.value === id) selectedSimulationId.value = null
  }

  async function renameEntry(id: string, name: string) {
    const updated = await renameSimulation(id, name)
    const idx = simulationHistory.value.findIndex(s => s.id === id)
    if (idx !== -1) simulationHistory.value[idx] = { ...simulationHistory.value[idx], name }
    if (currentResult.value?.id === id) currentResult.value = { ...currentResult.value, name: updated.name ?? name }
  }

  return {
    // State
    simulationHistory,
    currentResult,
    selectedSimulationId,
    // Actions
    loadHistory,
    loadSimulationById,
    deleteEntry,
    renameEntry,
  }
})
