import { defineStore } from 'pinia'
import {
  fetchReferential,
  createSupply,
  updateSupply,
  deleteSupply,
  createDemand,
  deleteDemand,
  createNetworkComponent,
  deleteNetworkComponent,
  runSimulation,
  fetchSimulations,
  fetchSimulationById,
  type Supply,
  type Demand,
  type NetworkComponent,
  type SimulationResult,
  type SimulationListItem,
  type SupplyCreate,
  type SupplyUpdate,
  type DemandCreate,
  type NetworkCreate,
} from '~/composables/api'

interface AssetEntry { id: string; overrides: Record<string, number> }

export const useSimulationStore = defineStore('simulation', () => {
  // ─── Assets disponibles en BDD ──────────────────────────────────────────────
  const availableSupplies = ref<Supply[]>([])
  const availableDemands = ref<Demand[]>([])
  const availableNetwork = ref<NetworkComponent[]>([])
  const referentialLoading = ref(false)
  const referentialLoaded = ref(false)

  // ─── Sélection courante avec overrides ──────────────────────────────────────
  const _supplyEntries = ref<AssetEntry[]>([])
  const _demandEntries = ref<AssetEntry[]>([])
  const _networkEntries = ref<AssetEntry[]>([])

  const selectedSupplyIds = computed(() => _supplyEntries.value.map(e => e.id))
  const selectedDemandIds = computed(() => _demandEntries.value.map(e => e.id))
  const selectedNetworkIds = computed(() => _networkEntries.value.map(e => e.id))

  // ─── Computed : objets sélectionnés ─────────────────────────────────────────
  const selectedSupplies = computed(() =>
    availableSupplies.value.filter(s => selectedSupplyIds.value.includes(s.id))
  )
  const selectedDemands = computed(() =>
    availableDemands.value.filter(d => selectedDemandIds.value.includes(d.id))
  )
  const selectedNetwork = computed(() =>
    availableNetwork.value.filter(n => selectedNetworkIds.value.includes(n.id))
  )

  // ─── État simulation ─────────────────────────────────────────────────────────
  const currentResult = ref<SimulationResult | null>(null)
  const simulationHistory = ref<SimulationListItem[]>([])
  const isRunning = ref(false)
  const error = ref<string | null>(null)
  const backendAvailable = ref<boolean | null>(null)

  // ─── Paramètres ──────────────────────────────────────────────────────────────
  const snapshotHours = ref(24)
  const solver = ref('highs')

  // ─── Chargement référentiel ──────────────────────────────────────────────────

  async function loadReferential() {
    referentialLoading.value = true
    error.value = null
    try {
      const data = await fetchReferential()
      availableSupplies.value = data.supplies
      availableDemands.value = data.demands
      availableNetwork.value = data.network
      referentialLoaded.value = true
      backendAvailable.value = true
    }
    catch {
      backendAvailable.value = false
      error.value = 'Backend unavailable — running in demo mode'
    }
    finally {
      referentialLoading.value = false
    }
  }

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
      // Collect overrides from all selected entries
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
      currentResult.value = result
      backendAvailable.value = true
      simulationHistory.value.unshift({
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

  // ─── CRUD Supply ─────────────────────────────────────────────────────────────

  async function addSupply(data: SupplyCreate) {
    const created = await createSupply(data)
    availableSupplies.value.push(created)
    return created
  }

  async function editSupply(id: string, data: SupplyUpdate) {
    const updated = await updateSupply(id, data)
    const idx = availableSupplies.value.findIndex(s => s.id === id)
    if (idx !== -1) availableSupplies.value[idx] = updated
    return updated
  }

  async function removeSupply(id: string) {
    await deleteSupply(id)
    availableSupplies.value = availableSupplies.value.filter(s => s.id !== id)
    removeSupplyFromSelection(id)
  }

  // ─── CRUD Demand ─────────────────────────────────────────────────────────────

  async function addDemand(data: DemandCreate) {
    const created = await createDemand(data)
    availableDemands.value.push(created)
    return created
  }

  async function removeDemand(id: string) {
    await deleteDemand(id)
    availableDemands.value = availableDemands.value.filter(d => d.id !== id)
    removeDemandFromSelection(id)
  }

  // ─── CRUD Network ────────────────────────────────────────────────────────────

  async function addNetworkComponent(data: NetworkCreate) {
    const created = await createNetworkComponent(data)
    availableNetwork.value.push(created)
    return created
  }

  async function removeNetworkComponent(id: string) {
    await deleteNetworkComponent(id)
    availableNetwork.value = availableNetwork.value.filter(n => n.id !== id)
    removeNetworkFromSelection(id)
  }

  return {
    // State
    availableSupplies,
    availableDemands,
    availableNetwork,
    selectedSupplyIds,
    selectedDemandIds,
    selectedNetworkIds,
    selectedSupplies,
    selectedDemands,
    selectedNetwork,
    referentialLoading,
    referentialLoaded,
    currentResult,
    simulationHistory,
    isRunning,
    error,
    backendAvailable,
    snapshotHours,
    solver,
    // Actions
    loadReferential,
    addSupplyToSelection,
    removeSupplyFromSelection,
    addDemandToSelection,
    removeDemandFromSelection,
    addNetworkToSelection,
    removeNetworkFromSelection,
    getOverrides,
    setOverride,
    clearOverrides,
    hasOverrides,
    runFullSimulation,
    loadHistory,
    loadSimulationById,
    addSupply,
    editSupply,
    removeSupply,
    addDemand,
    removeDemand,
    addNetworkComponent,
    removeNetworkComponent,
  }
})
