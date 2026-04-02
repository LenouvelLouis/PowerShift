import { defineStore } from "pinia";
import {
  runSimulation,
  type SimulationResult,
  type SimulationRunRequest,
  type DemandCreate,
  type NetworkCreate,
  type ScenarioExport,
  type SupplyCreate,
  type SupplyUpdate,
} from "~/composables/api";

/** Normalize a payload for equality comparison (sort IDs, ignore name). */
function _payloadKey(p: SimulationRunRequest): string {
  return JSON.stringify({
    supply_ids: [...p.supply_ids].sort(),
    demand_ids: [...p.demand_ids].sort(),
    network_ids: [...p.network_ids].sort(),
    snapshot_hours: p.snapshot_hours,
    solver: p.solver,
    asset_overrides: p.asset_overrides ?? null,
  });
}
import { useHistoryStore } from "~/stores/history";
import { useReferentialStore } from "~/stores/referential";

interface AssetEntry {
  id: string;
  assetOverrides: Record<string, number>;
}

export const useSimulationStore = defineStore("simulation", () => {
  const referential = useReferentialStore();
  const historyStore = useHistoryStore();

  // ─── Sélection courante avec overrides ──────────────────────────────────────
  const _supplyEntries = ref<AssetEntry[]>([]);
  const _demandEntries = ref<AssetEntry[]>([]);
  const _networkEntries = ref<AssetEntry[]>([]);

  const selectedSupplyIds = computed(() =>
    _supplyEntries.value.map((e) => e.id),
  );
  const selectedDemandIds = computed(() =>
    _demandEntries.value.map((e) => e.id),
  );
  const selectedNetworkIds = computed(() =>
    _networkEntries.value.map((e) => e.id),
  );

  // ─── Computed : objets sélectionnés ─────────────────────────────────────────
  const selectedSupplies = computed(() =>
    referential.availableSupplies.filter((s) =>
      selectedSupplyIds.value.includes(s.id),
    ),
  );
  const selectedDemands = computed(() =>
    referential.availableDemands.filter((d) =>
      selectedDemandIds.value.includes(d.id),
    ),
  );
  const selectedNetwork = computed(() =>
    referential.availableNetwork.filter((n) =>
      selectedNetworkIds.value.includes(n.id),
    ),
  );

  // ─── État simulation ─────────────────────────────────────────────────────────
  const isRunning = ref(false);
  const isLiveRunning = ref(false);
  const isSaving = ref(false);
  const error = ref<string | null>(null);
  const liveError = ref<string | null>(null);

  // ─── Résultats ───────────────────────────────────────────────────────────────
  // currentLiveResult — the result from the latest live preview (not saved)
  const currentLiveResult = ref<SimulationResult | null>(null);

  // selectedHistoryId — null = live mode, string = viewing a saved simulation
  const selectedHistoryId = ref<string | null>(null);

  const isLiveMode = computed(() => selectedHistoryId.value === null);

  // displayedResult — what the dashboard shows:
  //   live mode  → currentLiveResult (from /preview)
  //   history    → historyStore.currentResult (loaded by id)
  const displayedResult = computed<SimulationResult | null>(() =>
    isLiveMode.value ? currentLiveResult.value : historyStore.currentResult,
  );

  // ─── Paramètres ──────────────────────────────────────────────────────────────
  const snapshotHours = ref(24);
  const solver = ref("highs");
  const scenarioName = ref("");

  // ─── Référence de simulation sauvegardée ─────────────────────────────────────
  // Tracks the last saved/loaded simulation so we can detect parameter changes.
  const referenceSimId = ref<string | null>(null);
  const referencePayload = ref<SimulationRunRequest | null>(null);

  /** True when the current parameters match the last saved/loaded simulation. */
  const paramsMatchSaved = computed(() => {
    if (!referencePayload.value) return false;
    return _payloadKey(buildPayload()) === _payloadKey(referencePayload.value);
  });

  function setReference(id: string | null, payload: SimulationRunRequest | null) {
    referenceSimId.value = id;
    referencePayload.value = payload ? { ...payload } : null;
  }

  // ─── Live simulation helpers ──────────────────────────────────────────────────

  const hasMinimumAssets = computed(() =>
    _supplyEntries.value.length > 0 && _demandEntries.value.length > 0,
  );

  function buildPayload(): SimulationRunRequest {
    const assetOverrides: Record<string, Record<string, number>> = {};
    for (const e of [
      ..._supplyEntries.value,
      ..._demandEntries.value,
      ..._networkEntries.value,
    ]) {
      if (Object.keys(e.assetOverrides).length > 0)
        assetOverrides[e.id] = { ...e.assetOverrides };
    }
    return {
      supply_ids: selectedSupplyIds.value,
      demand_ids: selectedDemandIds.value,
      network_ids: selectedNetworkIds.value,
      snapshot_hours: snapshotHours.value,
      solver: solver.value,
      asset_overrides:
        Object.keys(assetOverrides).length > 0 ? assetOverrides : undefined,
    };
  }

  // ─── Gestion de la sélection ─────────────────────────────────────────────────

  function addSupplyToSelection(id: string) {
    if (!selectedSupplyIds.value.includes(id))
      _supplyEntries.value.push({ id, assetOverrides: {} });
  }
  function removeSupplyFromSelection(id: string) {
    _supplyEntries.value = _supplyEntries.value.filter((e) => e.id !== id);
  }
  function addDemandToSelection(id: string) {
    if (!selectedDemandIds.value.includes(id))
      _demandEntries.value.push({ id, assetOverrides: {} });
  }
  function removeDemandFromSelection(id: string) {
    _demandEntries.value = _demandEntries.value.filter((e) => e.id !== id);
  }
  function addNetworkToSelection(id: string) {
    if (!selectedNetworkIds.value.includes(id))
      _networkEntries.value.push({ id, assetOverrides: {} });
  }
  function removeNetworkFromSelection(id: string) {
    _networkEntries.value = _networkEntries.value.filter((e) => e.id !== id);
  }

  // ─── Overrides ───────────────────────────────────────────────────────────────

  function _entries(type: "supply" | "demand" | "network") {
    if (type === "supply") return _supplyEntries;
    if (type === "demand") return _demandEntries;
    return _networkEntries;
  }

  function getOverrides(
    type: "supply" | "demand" | "network",
    id: string,
  ): Record<string, number> {
    return _entries(type).value.find((e) => e.id === id)?.assetOverrides ?? {};
  }

  function setOverride(
    type: "supply" | "demand" | "network",
    id: string,
    field: string,
    value: number,
  ) {
    const entry = _entries(type).value.find((e) => e.id === id);
    if (entry) entry.assetOverrides[field] = value;
  }

  function clearOverrides(type: "supply" | "demand" | "network", id: string) {
    const entry = _entries(type).value.find((e) => e.id === id);
    if (entry) entry.assetOverrides = {};
  }

  function hasOverrides(
    type: "supply" | "demand" | "network",
    id: string,
  ): boolean {
    return Object.keys(getOverrides(type, id)).length > 0;
  }

  // ─── Simulation (full run — saves to DB) ─────────────────────────────────────

  async function runFullSimulation() {
    isRunning.value = true;
    error.value = null;
    try {
      // If a scenario with the same name already exists, delete it first (unique named scenarios)
      if (scenarioName.value) {
        const existing = historyStore.simulationHistory.find(
          (s) => s.name === scenarioName.value,
        );
        if (existing) {
          await historyStore.deleteEntry(existing.id);
        }
      }

      const result = await runSimulation({
        ...buildPayload(),
        name: scenarioName.value || undefined,
      });

      historyStore.currentResult = result;
      currentLiveResult.value = result;
      referential.backendAvailable = true;
      historyStore.simulationHistory.unshift({
        id: result.id,
        request_id: result.request_id,
        status: result.status,
        solver: result.solver,
        name: result.name ?? null,
        supply_ids: selectedSupplyIds.value.slice(),
        demand_ids: selectedDemandIds.value.slice(),
        network_ids: selectedNetworkIds.value.slice(),
        total_supply_mwh: result.total_supply_mwh,
        total_demand_mwh: result.total_demand_mwh,
        created_at: result.created_at,
      });
      return result;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Simulation failed";
      error.value = msg;
      throw e;
    } finally {
      isRunning.value = false;
    }
  }

  // ─── Scenario management ─────────────────────────────────────────────────────

  function clearScenario() {
    scenarioName.value = "";
    _supplyEntries.value = [];
    _demandEntries.value = [];
    _networkEntries.value = [];
    referenceSimId.value = null;
    referencePayload.value = null;
  }

  function loadFromScenario(scenario: ScenarioExport, name: string) {
    clearScenario();
    scenarioName.value = name;
    snapshotHours.value = scenario.snapshot_hours;
    const overrides = scenario.asset_overrides ?? {};
    for (const id of scenario.supply_ids)
      _supplyEntries.value.push({
        id,
        assetOverrides: { ...(overrides[id] ?? {}) },
      });
    for (const id of scenario.demand_ids)
      _demandEntries.value.push({
        id,
        assetOverrides: { ...(overrides[id] ?? {}) },
      });
    for (const id of scenario.network_ids)
      _networkEntries.value.push({
        id,
        assetOverrides: { ...(overrides[id] ?? {}) },
      });
  }

  // ─── Wrapper CRUD : Supply ────────────────────────────────────────────────────

  async function addSupply(data: SupplyCreate) {
    return referential.addSupply(data);
  }

  async function editSupply(id: string, data: SupplyUpdate) {
    return referential.editSupply(id, data);
  }

  async function removeSupply(id: string) {
    await referential.removeSupply(id);
    removeSupplyFromSelection(id);
  }

  // ─── Wrapper CRUD : Demand ────────────────────────────────────────────────────

  async function addDemand(data: DemandCreate) {
    return referential.addDemand(data);
  }

  async function removeDemand(id: string) {
    await referential.removeDemand(id);
    removeDemandFromSelection(id);
  }

  // ─── Wrapper CRUD : Network ───────────────────────────────────────────────────

  async function addNetworkComponent(data: NetworkCreate) {
    return referential.addNetworkComponent(data);
  }

  async function removeNetworkComponent(id: string) {
    await referential.removeNetworkComponent(id);
    removeNetworkFromSelection(id);
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
    isLiveRunning,
    isSaving,
    error,
    liveError,
    snapshotHours,
    solver,
    scenarioName,
    // Live mode
    currentLiveResult,
    selectedHistoryId,
    isLiveMode,
    displayedResult,
    hasMinimumAssets,
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
    // Reference sim tracking
    referenceSimId,
    paramsMatchSaved,
    setReference,
    // Actions — simulation
    runFullSimulation,
    buildPayload,
    clearScenario,
    loadFromScenario,
    // Actions — CRUD wrappers
    addSupply,
    editSupply,
    removeSupply,
    addDemand,
    removeDemand,
    addNetworkComponent,
    removeNetworkComponent,
  };
});
