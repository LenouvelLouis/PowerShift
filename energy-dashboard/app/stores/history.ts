import { defineStore } from 'pinia'
import {
  fetchSimulations,
  fetchSimulationById,
  type SimulationResult,
  type SimulationListItem,
} from '~/composables/api'

export const useHistoryStore = defineStore('history', () => {
  // ─── État ────────────────────────────────────────────────────────────────────
  const simulationHistory = ref<SimulationListItem[]>([])
  const currentResult = ref<SimulationResult | null>(null)

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
  }

  return {
    // State
    simulationHistory,
    currentResult,
    // Actions
    loadHistory,
    loadSimulationById,
  }
})
