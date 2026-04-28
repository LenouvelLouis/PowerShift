import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useHistoryStore } from '~/stores/history'
import {
  fetchSimulations,
  deleteSimulation,
  renameSimulation
} from '~/composables/api'

// Mock the API composable — vitest hoists vi.mock above imports automatically
vi.mock('~/composables/api', () => ({
  fetchSimulations: vi.fn(),
  fetchSimulationById: vi.fn(),
  deleteSimulation: vi.fn(),
  renameSimulation: vi.fn()
}))

const mockFetchSimulations = vi.mocked(fetchSimulations)
const mockDeleteSimulation = vi.mocked(deleteSimulation)
const mockRenameSimulation = vi.mocked(renameSimulation)

function makeListItem(overrides: Record<string, unknown> = {}) {
  return {
    id: 'sim-1',
    request_id: 'req-1',
    status: 'converged' as const,
    solver: 'highs',
    name: 'Test Sim',
    supply_ids: ['s1'],
    demand_ids: ['d1'],
    network_ids: [],
    total_supply_mwh: 100,
    total_demand_mwh: 80,
    created_at: '2026-01-01T00:00:00Z',
    ...overrides
  }
}

describe('useHistoryStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('loadHistory', () => {
    it('populates simulationHistory from API', async () => {
      const items = [makeListItem(), makeListItem({ id: 'sim-2', name: 'Sim 2' })]
      mockFetchSimulations.mockResolvedValue({ items, total: 2, page: 1, size: 20, pages: 1 })

      const store = useHistoryStore()
      await store.loadHistory()

      expect(store.simulationHistory).toHaveLength(2)
      expect(store.simulationHistory[0]!.id).toBe('sim-1')
      expect(store.simulationHistory[1]!.id).toBe('sim-2')
    })

    it('does not throw on API error', async () => {
      mockFetchSimulations.mockRejectedValue(new Error('Network error') as never)

      const store = useHistoryStore()
      await expect(store.loadHistory()).resolves.toBeUndefined()
      expect(store.simulationHistory).toHaveLength(0)
    })
  })

  describe('deleteEntry', () => {
    it('removes entry from simulationHistory', async () => {
      mockDeleteSimulation.mockResolvedValue(undefined)

      const store = useHistoryStore()
      store.simulationHistory = [
        makeListItem({ id: 'sim-1' }),
        makeListItem({ id: 'sim-2' })
      ]

      await store.deleteEntry('sim-1')

      expect(store.simulationHistory).toHaveLength(1)
      expect(store.simulationHistory[0]!.id).toBe('sim-2')
    })

    it('clears currentResult when deleting the active simulation', async () => {
      mockDeleteSimulation.mockResolvedValue(undefined)

      const store = useHistoryStore()
      store.simulationHistory = [makeListItem({ id: 'sim-1' })]
      store.currentResult = {
        id: 'sim-1',
        request_id: 'req-1',
        status: 'converged',
        solver: 'highs',
        total_supply_mwh: 100,
        total_demand_mwh: 80,
        balance_mwh: 20,
        objective_value: null,
        result_json: null,
        created_at: '2026-01-01T00:00:00Z'
      }

      await store.deleteEntry('sim-1')

      expect(store.currentResult).toBeNull()
    })
  })

  describe('renameEntry', () => {
    it('updates the name in simulationHistory', async () => {
      mockRenameSimulation.mockResolvedValue({
        id: 'sim-1',
        request_id: 'req-1',
        status: 'converged',
        solver: 'highs',
        name: 'Renamed Sim',
        total_supply_mwh: 100,
        total_demand_mwh: 80,
        balance_mwh: 20,
        objective_value: null,
        result_json: null,
        created_at: '2026-01-01T00:00:00Z'
      })

      const store = useHistoryStore()
      store.simulationHistory = [makeListItem({ id: 'sim-1', name: 'Old Name' })]

      await store.renameEntry('sim-1', 'Renamed Sim')

      expect(store.simulationHistory[0]!.name).toBe('Renamed Sim')
    })

    it('updates currentResult name when renaming active simulation', async () => {
      mockRenameSimulation.mockResolvedValue({
        id: 'sim-1',
        request_id: 'req-1',
        status: 'converged',
        solver: 'highs',
        name: 'New Name',
        total_supply_mwh: 100,
        total_demand_mwh: 80,
        balance_mwh: 20,
        objective_value: null,
        result_json: null,
        created_at: '2026-01-01T00:00:00Z'
      })

      const store = useHistoryStore()
      store.simulationHistory = [makeListItem({ id: 'sim-1' })]
      store.currentResult = {
        id: 'sim-1',
        request_id: 'req-1',
        status: 'converged',
        solver: 'highs',
        name: 'Old Name',
        total_supply_mwh: 100,
        total_demand_mwh: 80,
        balance_mwh: 20,
        objective_value: null,
        result_json: null,
        created_at: '2026-01-01T00:00:00Z'
      }

      await store.renameEntry('sim-1', 'New Name')

      expect(store.currentResult!.name).toBe('New Name')
    })
  })
})
