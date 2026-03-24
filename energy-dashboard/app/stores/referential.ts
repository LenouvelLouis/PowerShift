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
  type Supply,
  type Demand,
  type NetworkComponent,
  type SupplyCreate,
  type SupplyUpdate,
  type DemandCreate,
  type NetworkCreate,
} from '~/composables/api'

export const useReferentialStore = defineStore('referential', () => {
  // ─── Assets disponibles en BDD ──────────────────────────────────────────────
  const availableSupplies = ref<Supply[]>([])
  const availableDemands = ref<Demand[]>([])
  const availableNetwork = ref<NetworkComponent[]>([])
  const referentialLoading = ref(false)
  const referentialLoaded = ref(false)
  const backendAvailable = ref<boolean | null>(null)

  // ─── Chargement référentiel ──────────────────────────────────────────────────

  async function loadReferential() {
    referentialLoading.value = true
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
    }
    finally {
      referentialLoading.value = false
    }
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
  }

  // ─── CRUD Network ─────────────────────────────────────────────────────────────

  async function addNetworkComponent(data: NetworkCreate) {
    const created = await createNetworkComponent(data)
    availableNetwork.value.push(created)
    return created
  }

  async function removeNetworkComponent(id: string) {
    await deleteNetworkComponent(id)
    availableNetwork.value = availableNetwork.value.filter(n => n.id !== id)
  }

  return {
    // State
    availableSupplies,
    availableDemands,
    availableNetwork,
    referentialLoading,
    referentialLoaded,
    backendAvailable,
    // Actions
    loadReferential,
    addSupply,
    editSupply,
    removeSupply,
    addDemand,
    removeDemand,
    addNetworkComponent,
    removeNetworkComponent,
  }
})
