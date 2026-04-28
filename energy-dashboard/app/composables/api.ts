/**
 * API composable — typed $fetch wrappers for all backend endpoints.
 * All calls go through the Nuxt proxy: /api/** → http://backend:8000/api/**
 */

// ─── TypeScript interfaces (mirrors backend Pydantic schemas) ─────────────────

export type ComponentStatus = 'active' | 'inactive' | 'maintenance'

export interface Supply {
  id: string
  name: string
  type: 'wind_turbine' | 'solar_panel' | 'nuclear_plant'
  capacity_mw: number
  efficiency: number
  status: ComponentStatus
  unit: string
  description: string
  carrier: string
  created_at: string
  updated_at: string
}

export type SupplyCreate = Omit<
  Supply,
  'id' | 'created_at' | 'updated_at' | 'carrier'
>
export type SupplyUpdate = Partial<
  Omit<Supply, 'id' | 'created_at' | 'updated_at' | 'carrier' | 'type'>
>

export interface Demand {
  id: string
  name: string
  type: 'house' | 'electric_vehicle'
  load_mw: number
  status: ComponentStatus
  unit: string
  description: string
  created_at: string
  updated_at: string
}

export type DemandCreate = Omit<Demand, 'id' | 'created_at' | 'updated_at'>
export type DemandUpdate = Partial<
  Omit<Demand, 'id' | 'created_at' | 'updated_at' | 'type'>
>

export interface NetworkComponent {
  id: string
  name: string
  type: 'transformer' | 'cable'
  voltage_kv: number
  capacity_mva: number
  losses_kw: number | null
  voltage_hv_kv: number | null
  voltage_lv_kv: number | null
  length_km: number | null
  resistance_ohm_per_km: number | null
  reactance_ohm_per_km: number | null
  status: ComponentStatus
  unit: string
  description: string
  created_at: string
  updated_at: string
}

export type NetworkCreate = Omit<
  NetworkComponent,
  'id' | 'created_at' | 'updated_at'
>

export interface Referential {
  supplies: Supply[]
  demands: Demand[]
  network: NetworkComponent[]
}

export interface SimulationRunRequest {
  supply_ids: string[]
  demand_ids: string[]
  network_ids: string[]
  snapshot_hours: number
  solver: string
  optimization_objective?: 'min_cost' | 'min_emissions' | 'max_renewable'
  name?: string
  start_date?: string
  end_date?: string
  pypsa_params?: Record<string, unknown>
  asset_overrides?: Record<string, Record<string, number>>
}

export interface SimulationResultJson {
  // Power flow / OPF time-series
  generators_t: Record<string, { p: number[], q?: number[] }>
  storage_units_t?: Record<string, { p: number[], state_of_charge: number[] }>
  loads_t: Record<string, { p: number[], q?: number[] }>
  buses_t?: Record<string, { v_mag_pu: number[], v_ang: number[] }>
  lines_t?: Record<string, { p0: number[], loading: number[] }>
  // Aggregates
  capacity_factors: Record<string, number>
  convergence?: {
    all_converged: boolean
    converged_count: number
    total_snapshots: number
    non_converged_snapshots: number[]
  }
  grid_exchange?: {
    import_export_mw: number[]
    total_import_mwh: number
    total_export_mwh: number
  }
  violations?: { overloads: unknown[], overvoltages: unknown[] }
  // Error fields
  error?: string
  error_type?: 'convergence_error' | 'runtime_error'
  warnings?: string[]
}

export interface SimulationResult {
  id: string
  request_id: string
  status: 'converged' | 'optimized' | 'non_converged' | 'error'
  solver: string
  name?: string | null
  start_date?: string | null
  end_date?: string | null
  total_supply_mwh: number | null
  total_demand_mwh: number | null
  balance_mwh: number | null
  objective_value: number | null
  result_json: SimulationResultJson | null
  created_at: string
}

export interface SimulationListItem {
  id: string
  request_id: string
  status: 'converged' | 'optimized' | 'non_converged' | 'error'
  solver: string
  name?: string | null
  supply_ids: string[]
  demand_ids: string[]
  network_ids: string[]
  total_supply_mwh: number | null
  total_demand_mwh: number | null
  created_at: string
}

export interface SimulationSolverInfo {
  name: string
  available: boolean
  reason?: string | null
}

// ─── Supply ───────────────────────────────────────────────────────────────────

export const fetchSupplies = () => $fetch<Supply[]>('/api/v1/supplies')

export const fetchSupplyById = (id: string) =>
  $fetch<Supply>(`/api/v1/supplies/${id}`)

export const createSupply = (data: SupplyCreate) =>
  $fetch<Supply>('/api/v1/supplies', { method: 'POST', body: data })

export const updateSupply = (id: string, data: SupplyUpdate) =>
  $fetch<Supply>(`/api/v1/supplies/${id}`, { method: 'PUT', body: data })

export const deleteSupply = (id: string) =>
  $fetch<undefined>(`/api/v1/supplies/${id}`, { method: 'DELETE' })

// ─── Demand ───────────────────────────────────────────────────────────────────

export const fetchDemands = () => $fetch<Demand[]>('/api/v1/demands')

export const fetchDemandById = (id: string) =>
  $fetch<Demand>(`/api/v1/demands/${id}`)

export const createDemand = (data: DemandCreate) =>
  $fetch<Demand>('/api/v1/demands', { method: 'POST', body: data })

export const deleteDemand = (id: string) =>
  $fetch<undefined>(`/api/v1/demands/${id}`, { method: 'DELETE' })

// ─── Network ──────────────────────────────────────────────────────────────────

export const fetchNetwork = () => $fetch<NetworkComponent[]>('/api/v1/network')

export const createNetworkComponent = (data: NetworkCreate) =>
  $fetch<NetworkComponent>('/api/v1/network', { method: 'POST', body: data })

export const deleteNetworkComponent = (id: string) =>
  $fetch<undefined>(`/api/v1/network/${id}`, { method: 'DELETE' })

// ─── Referential ──────────────────────────────────────────────────────────────

export const fetchReferential = () =>
  $fetch<Referential>('/api/v1/referential')

export interface ScenarioExport {
  scenario_version: string
  snapshot_hours: number
  solver: string
  start_date?: string | null
  end_date?: string | null
  supply_ids: string[]
  demand_ids: string[]
  network_ids: string[]
  asset_overrides?: Record<string, Record<string, number>> | null
}

// ─── Simulation ───────────────────────────────────────────────────────────────

export const saveSimulation = (params: SimulationRunRequest) =>
  $fetch<SimulationResult>('/api/v1/simulation/save', {
    method: 'POST',
    body: params
  })

/** Run PyPSA without writing to the database — for live frontend preview. */
export const previewSimulation = (params: SimulationRunRequest) =>
  $fetch<SimulationResult>('/api/v1/simulation/preview', { method: 'POST', body: params })

export const fetchSimulations = () =>
  $fetch<SimulationListItem[]>('/api/v1/simulation')

export const fetchSimulationById = (id: string) =>
  $fetch<SimulationResult>(`/api/v1/simulation/${id}`)

export const renameSimulation = (id: string, name: string) =>
  $fetch<SimulationResult>(`/api/v1/simulation/${id}/rename`, {
    method: 'PATCH',
    body: { name }
  })

export const deleteSimulation = (id: string) =>
  $fetch<undefined>(`/api/v1/simulation/${id}`, { method: 'DELETE' })

export const fetchScenarioExport = (id: string) =>
  $fetch<ScenarioExport>(`/api/v1/simulation/${id}/export`)

export const fetchSimulationSolvers = () =>
  $fetch<SimulationSolverInfo[]>('/api/v1/simulation/solvers')
