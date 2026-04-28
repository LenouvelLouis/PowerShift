import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSimulationStore } from '~/stores/simulation'

describe('useSimulationStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('addSupplyToSelection / removeSupplyFromSelection', () => {
    it('adds a supply id to the selection', () => {
      const store = useSimulationStore()
      store.addSupplyToSelection('s1')
      expect(store.selectedSupplyIds).toContain('s1')
    })

    it('does not add duplicates', () => {
      const store = useSimulationStore()
      store.addSupplyToSelection('s1')
      store.addSupplyToSelection('s1')
      expect(store.selectedSupplyIds).toHaveLength(1)
    })

    it('removes a supply from the selection', () => {
      const store = useSimulationStore()
      store.addSupplyToSelection('s1')
      store.addSupplyToSelection('s2')
      store.removeSupplyFromSelection('s1')
      expect(store.selectedSupplyIds).toEqual(['s2'])
    })
  })

  describe('addDemandToSelection / removeDemandFromSelection', () => {
    it('adds and removes demand ids', () => {
      const store = useSimulationStore()
      store.addDemandToSelection('d1')
      expect(store.selectedDemandIds).toContain('d1')
      store.removeDemandFromSelection('d1')
      expect(store.selectedDemandIds).toHaveLength(0)
    })
  })

  describe('addNetworkToSelection / removeNetworkFromSelection', () => {
    it('adds and removes network ids', () => {
      const store = useSimulationStore()
      store.addNetworkToSelection('n1')
      expect(store.selectedNetworkIds).toContain('n1')
      store.removeNetworkFromSelection('n1')
      expect(store.selectedNetworkIds).toHaveLength(0)
    })
  })

  describe('hasMinimumAssets', () => {
    it('returns false when no assets selected', () => {
      const store = useSimulationStore()
      expect(store.hasMinimumAssets).toBe(false)
    })

    it('returns false when only supplies are selected', () => {
      const store = useSimulationStore()
      store.addSupplyToSelection('s1')
      expect(store.hasMinimumAssets).toBe(false)
    })

    it('returns false when only demands are selected', () => {
      const store = useSimulationStore()
      store.addDemandToSelection('d1')
      expect(store.hasMinimumAssets).toBe(false)
    })

    it('returns true when at least one supply and one demand', () => {
      const store = useSimulationStore()
      store.addSupplyToSelection('s1')
      store.addDemandToSelection('d1')
      expect(store.hasMinimumAssets).toBe(true)
    })
  })

  describe('buildPayload', () => {
    it('returns correct shape with defaults', () => {
      const store = useSimulationStore()
      store.addSupplyToSelection('s1')
      store.addDemandToSelection('d1')
      store.addNetworkToSelection('n1')

      const payload = store.buildPayload()

      expect(payload).toMatchObject({
        supply_ids: ['s1'],
        demand_ids: ['d1'],
        network_ids: ['n1'],
        snapshot_hours: 24,
        solver: 'highs',
        optimization_objective: 'min_cost'
      })
      // No overrides by default
      expect(payload.asset_overrides).toBeUndefined()
    })

    it('includes asset_overrides when set', () => {
      const store = useSimulationStore()
      store.addSupplyToSelection('s1')
      store.addDemandToSelection('d1')
      store.setOverride('supply', 's1', 'capacity_mw', 500)

      const payload = store.buildPayload()

      expect(payload.asset_overrides).toEqual({
        s1: { capacity_mw: 500 }
      })
    })

    it('includes start_date and end_date when set', () => {
      const store = useSimulationStore()
      store.addSupplyToSelection('s1')
      store.addDemandToSelection('d1')
      store.startDate = '2026-01-01'
      store.endDate = '2026-01-07'

      const payload = store.buildPayload()

      expect(payload.start_date).toBe('2026-01-01')
      expect(payload.end_date).toBe('2026-01-07')
    })
  })

  describe('clearScenario', () => {
    it('resets all state', () => {
      const store = useSimulationStore()
      store.addSupplyToSelection('s1')
      store.addDemandToSelection('d1')
      store.addNetworkToSelection('n1')
      store.scenarioName = 'Test Scenario'
      store.startDate = '2026-01-01'
      store.endDate = '2026-12-31'

      store.clearScenario()

      expect(store.selectedSupplyIds).toHaveLength(0)
      expect(store.selectedDemandIds).toHaveLength(0)
      expect(store.selectedNetworkIds).toHaveLength(0)
      expect(store.scenarioName).toBe('')
      expect(store.startDate).toBe('')
      expect(store.endDate).toBe('')
    })
  })

  describe('overrides', () => {
    it('getOverrides returns empty object when no overrides set', () => {
      const store = useSimulationStore()
      store.addSupplyToSelection('s1')
      expect(store.getOverrides('supply', 's1')).toEqual({})
    })

    it('setOverride and getOverrides work together', () => {
      const store = useSimulationStore()
      store.addSupplyToSelection('s1')
      store.setOverride('supply', 's1', 'capacity_mw', 200)
      expect(store.getOverrides('supply', 's1')).toEqual({ capacity_mw: 200 })
    })

    it('hasOverrides returns correct boolean', () => {
      const store = useSimulationStore()
      store.addSupplyToSelection('s1')
      expect(store.hasOverrides('supply', 's1')).toBe(false)
      store.setOverride('supply', 's1', 'efficiency', 0.9)
      expect(store.hasOverrides('supply', 's1')).toBe(true)
    })

    it('clearOverrides removes all overrides for an asset', () => {
      const store = useSimulationStore()
      store.addSupplyToSelection('s1')
      store.setOverride('supply', 's1', 'capacity_mw', 200)
      store.setOverride('supply', 's1', 'efficiency', 0.9)
      store.clearOverrides('supply', 's1')
      expect(store.getOverrides('supply', 's1')).toEqual({})
    })
  })
})
