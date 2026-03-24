import { defineStore } from 'pinia'
import {
  runSimulation,
  type SupplyCreate,
  type SupplyUpdate,
  type DemandCreate,
  type NetworkCreate,
} from '~/composables/api'
import { useReferentialStore } from '~/stores/referential'
import { useHistoryStore } from '~/stores/history'

interface AssetEntry { id: string; overrides: Record<string, number> }

export const useSimulationStore = defineStore('simulation', () => {
  const referential = useReferentialStore()
  const historyStore = useHistoryStore()

  // ─── Sélection courante avec overrides ──────────────────────────────────────
  const _supplyEntries = ref<AssetEntry[]>([])
  const _demandEntries = ref<AssetEntry[]>([])
  const _networkEntries = ref<AssetEntry[]>([])

  const selectedSupplyIds = computed(() => _supplyEntries.value.map(e => e.id))
  const selectedDemandIds = computed(() => _demandEntries.value.map(e => e.id))
  const selectedNetworkIds = computed(() => _networkEntries.value.map(e => e.id))

  // ─── Computed : objets sélectionnés ─────────────────────────────────────────
  const selectedSupplies = computed(() =>
    referential.availableSupplies.filter(s => selectedSupplyIds.value.includes(s.id))
  )
  const selectedDemands = computed(() =>
    referential.availableDemands.filter(d => selectedDemandIds.value.includes(d.id))
  )
  const selectedNetwork = computed(() =>
    referential.availableNetwork.filter(n => selectedNetworkIds.value.includes(n.id))
  )

  // ─── État simulation ─────────────────────────────────────────────────────────
  const isRunning = ref(false)
  const error = ref<string | null>(null)

  // ─── Paramètres ──────────────────────────────────────────────────────────────
  const snapshotHours = ref(24)
  const solver = ref('highs')

  // ─── Gestion de la sélection ─────────────────────────────────────────────────

  function addSupplyToSelection(id: string) {
    if (!selectedSupplyIds.value.includes(id)) _supplyEntries.value.push({ id, overrides: {} })
  }
  function removeSupplyFromSelection(id: string) {
    _supplyEntries.value = _supplyEntries.value.filter(e => e.id !== id)
  }
  function addDemandToSelection(id: string) {
    if (!selectedDemandIds.value.includes(id)) _demandEntries.value.push({ id, overrides: {} })
  }
  function removeDemandFromSelection(id: string) {
    _demandEntries.value = _demandEntries.value.filter(e => e.id !== id)
  }
  function addNetworkToSelection(id: string) {
    if (!selectedNetworkIds.value.includes(id)) _networkEntries.value.push({ id, overrides: {} })
  }
  function removeNetworkFromSelection(id: string) {
    _networkEntries.value = _networkEntries.value.filter(e => e.id !== id)
  }

  // ─── Overrides ───────────────────────────────────────────────────────────────

  function _entries(type: 'supply' | 'demand' | 'network') {
    if (type === 'supply') return _supplyEntries
    if (type === 'demand') return _demandEntries
    return _networkEntries
  }

  function getOverrides(type: 'supply' | 'demand' | 'network', id: string): Record<string, number> {
    return _entries(type).value.find(e => e.id === id)?.overrides ?? {}
  }

  function setOverride(type: 'supply' | 'demand' | 'network', id: string, field: string, value: number) {
    const entry = _entries(type).value.find(e => e.id === id)
    if (entry) entry.overrides[field] = value
  }

  function clearOverrides(type: 'supply' | 'demand' | 'network', id: string) {
    const entry = _entries(type).value.find(e => e.id === id)
    if (entry) entry.overrides = {}
  }

  function hasOverrides(type: 'supply' | 'demand' | 'network', id: string): boolean {
    return Object.keys(getOverrides(type, id)).length > 0
  }

  // ─── Simulation ──────────────────────────────────────────────────────────────

  async function runFullSimulation() {
    isRunning.value = true
    error.value = null
    try {
      const overrides: Record<string, Record<string, number>> = {}
      for (const e of [..._supplyEntries.value, ..._demandEntries.value, ..._networkEntries.value]) {
        if (Object.keys(e.overrides).length > 0) overrides[e.id] = { ...e.overrides }
      }

      const result = await runSimulation({
        supply_ids: selectedSupplyIds.value,
        demand_ids: selectedDemandIds.value,
        network_ids: selectedNetworkIds.value,
        snapshot_hours: snapshotHours.value,
        solver: solver.value,
        overrides: Object.keys(overrides).length > 0 ? overrides : undefined,
      })

      historyStore.currentResult = result
      referential.backendAvailable = true
      historyStore.simulationHistory.unshift({
        id: result.id,
        request_id: result.request_id,
        status: result.status,
        supply_ids: selectedSupplyIds.value.slice(),
        demand_ids: selectedDemandIds.value.slice(),
        network_ids: selectedNetworkIds.value.slice(),
        total_supply_mwh: result.total_supply_mwh,
        total_demand_mwh: result.total_demand_mwh,
        created_at: result.created_at,
      })
      return result
    }
    catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Simulation failed'
      error.value = msg
      throw e
    }
    finally {
      isRunning.value = false
    }
  }

  // ─── Wrapper CRUD : Supply ────────────────────────────────────────────────────

  async function addSupply(data: SupplyCreate) {
    return referential.addSupply(data)
  }

  async function editSupply(id: string, data: SupplyUpdate) {
    return referential.editSupply(id, data)
  }

  async function removeSupply(id: string) {
    await referential.removeSupply(id)
    removeSupplyFromSelection(id)
  }

  // ─── Wrapper CRUD : Demand ────────────────────────────────────────────────────

  async function addDemand(data: DemandCreate) {
    return referential.addDemand(data)
  }

  async function removeDemand(id: string) {
    await referential.removeDemand(id)
    removeDemandFromSelection(id)
  }

  // ─── Wrapper CRUD : Network ───────────────────────────────────────────────────

  async function addNetworkComponent(data: NetworkCreate) {
    return referential.addNetworkComponent(data)
  }

  async function removeNetworkComponent(id: string) {
    await referential.removeNetworkComponent(id)
    removeNetworkFromSelection(id)
  }

  return {
    // State
    selectedSupplyIds,
    selectedDemandIds,
    selectedNetworkIds,
    selectedSupplies,
    selectedDemands,
    selectedNetwork,
    isRunning,
    error,
    snapshotHours,
    solver,
    // Actions — selection
    addSupplyToSelection,
    removeSupplyFromSelection,
    addDemandToSelection,
    removeDemandFromSelection,
    addNetworkToSelection,
    removeNetworkFromSelection,
    // Actions — overrides
    getOverrides,
    setOverride,
    clearOverrides,
    hasOverrides,
    // Actions — simulation
    runFullSimulation,
    // Actions — CRUD wrappers
    addSupply,
    editSupply,
    removeSupply,
    addDemand,
    removeDemand,
    addNetworkComponent,
    removeNetworkComponent,
  }
})
