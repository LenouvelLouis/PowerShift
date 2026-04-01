<template>
  <div class="flex flex-col h-screen bg-[#020617] text-white">
    <!-- Toast notifications (@nuxt/ui v4) -->
    <UToaster />

    <!-- Delete asset confirmation modal -->
    <UModal v-model:open="showDeleteModal">
      <template #header>
        <h3 class="text-base font-semibold text-white">Delete asset</h3>
      </template>
      <template #body>
        <p class="text-sm text-gray-300">
          Are you sure you want to permanently delete
          <span class="font-semibold text-white">{{ deleteTarget?.name }}</span
          >? This action cannot be undone.
        </p>
      </template>
      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton
            label="Cancel"
            color="neutral"
            variant="ghost"
            @click="deleteTarget = null"
          />
          <UButton
            label="Delete"
            color="error"
            :loading="isDeleting"
            @click="handleDeleteAsset"
          />
        </div>
      </template>
    </UModal>

    <!-- Solver helper modal -->
    <UModal v-model:open="showSolverHelpModal">
      <template #header>
        <div class="flex items-center justify-between gap-3 w-full">
          <div>
            <h3 class="text-base font-semibold text-white">Solver helper</h3>
            <p class="text-xs text-gray-400 mt-0.5">
              Quick guide to choose the best optimization solver.
            </p>
          </div>
          <span class="text-xs px-2 py-1 rounded bg-[#1E293B] text-slate-300">
            Selected: {{ selectedSolverLabel }}
          </span>
        </div>
      </template>
      <template #body>
        <div class="space-y-2 max-h-[60vh] overflow-y-auto pr-1">
          <div
            v-for="solver in solverOptions"
            :key="solver.value"
            class="rounded-lg border border-[#1E293B] bg-[#0B1220] p-3"
            :class="
              solver.value === store.solver ? 'ring-1 ring-[#3C83F8]/60' : ''
            "
          >
            <div class="flex items-center justify-between gap-3 mb-1">
              <p class="text-sm font-semibold text-white">
                {{ solver.label }}
              </p>
              <div class="flex items-center gap-1.5">
                <span
                  class="text-[11px] px-1.5 py-0.5 rounded bg-[#1E293B] text-slate-300"
                  >{{ solver.license }}</span
                >
                <span
                  class="text-[11px] px-1.5 py-0.5 rounded bg-[#1E293B] text-slate-300"
                  >{{ solver.speed }}</span
                >
              </div>
            </div>
            <p class="text-xs text-slate-300">
              {{ solver.description }}
            </p>
            <p class="text-xs text-gray-400 mt-1.5">
              Best for: {{ solver.bestFor }}
            </p>
          </div>
        </div>
      </template>
      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton
            label="Close"
            color="neutral"
            variant="ghost"
            @click="showSolverHelpModal = false"
          />
        </div>
      </template>
    </UModal>

    <!-- Header -->
    <header
      class="bg-[#0F172A] flex items-center justify-between px-4 gap-2 h-14 border-b border-gray-200 dark:border-gray-800 shrink-0"
    >
      <UButton
        variant="ghost"
        icon="i-heroicons-bars-3"
        @click="sidebarOpen = !sidebarOpen"
      />
      <img src="/logo.png" alt="EnergyDash" class="h-10 w-auto" />
      <span class="font-bold text-lg mr-50">Energy Network Simulator 2026</span>

      <!-- Statut backend -->
      <span
        class="text-xs px-2 py-1 rounded-full"
        :class="
          referential.backendAvailable === true
            ? 'bg-emerald-900/40 text-emerald-400'
            : referential.backendAvailable === false
              ? 'bg-red-900/40 text-red-400'
              : 'bg-gray-800 text-gray-500'
        "
      >
        {{
          referential.backendAvailable === true
            ? "● API"
            : referential.backendAvailable === false
              ? "● Demo"
              : "● …"
        }}
      </span>

      <!-- Sélecteur heures -->
      <div class="flex items-center gap-1.5">
        <label class="text-xs text-gray-400">Hours:</label>
        <USelect
          v-model="store.snapshotHours"
          :items="[
            { label: '1h', value: 1 },
            { label: '24h', value: 24 },
            { label: '168h', value: 168 },
            { label: '8760h', value: 8760 },
          ]"
          class="w-24"
          size="sm"
        />
      </div>

      <!-- Sélecteur solver -->
      <div class="flex items-center gap-1.5" :title="selectedSolverTitle">
        <label class="text-xs text-gray-400">Solver:</label>
        <USelect
          v-model="store.solver"
          :items="solverSelectItems"
          class="w-36"
          size="sm"
        />
        <UButton
          icon="i-heroicons-question-mark-circle"
          size="sm"
          color="neutral"
          variant="ghost"
          title="Open solver helper"
          @click="showSolverHelpModal = true"
        />
      </div>

      <!-- Scenario name + rename -->
      <div class="flex items-center gap-1">
        <UInput
          v-model="store.scenarioName"
          placeholder="Scenario name (optional)"
          size="sm"
          class="w-44"
        />
        <UButton
          icon="i-heroicons-pencil-square"
          size="sm"
          color="neutral"
          variant="ghost"
          title="Rename selected scenario"
          :disabled="!history.selectedSimulationId"
          @click="handleHeaderRename"
        />
      </div>

      <!-- Play / Stop / Import / Export -->
      <input
        ref="fileInput"
        type="file"
        accept=".json"
        class="hidden"
        @change="handleImport"
      />
      <UButton
        icon="i-heroicons-play"
        color="success"
        :label="store.isRunning ? 'Running…' : 'Play'"
        :loading="store.isRunning"
        :disabled="store.isRunning"
        @click="handlePlay"
      />
      <UButton
        icon="i-heroicons-stop"
        color="error"
        label="Stop"
        size="sm"
        :disabled="!store.isRunning"
      />
      <UButton
        icon="i-heroicons-arrow-up-tray"
        label="Import"
        class="bg-[#1E293B] hover:bg-[#2d3f55] text-white ml-auto"
        @click="fileInput?.click()"
      />
      <UButton
        icon="i-heroicons-arrow-down-tray"
        label="Export"
        class="bg-[#1E293B] hover:bg-[#2d3f55] text-white"
        :disabled="!history.currentResult && !history.selectedSimulationId"
        @click="handleExport"
      />
    </header>

    <div class="flex flex-1 overflow-hidden">
      <Transition name="sidebar">
        <aside
          v-if="sidebarOpen"
          class="bg-[#0F172A] w-60 border-r border-gray-200 dark:border-gray-800 flex flex-col shrink-0 overflow-hidden"
        >
          <div class="w-60 flex flex-col bg-[#0F172A] h-full">
            <!-- Onglets groupe -->
            <div class="flex flex-row border-b border-[#1E293B]">
              <button
                v-for="group in tabGroups"
                :key="group"
                class="flex-1 flex items-center justify-center gap-1 py-2 text-xs font-bold uppercase tracking-wider transition-all duration-200 cursor-pointer"
                :class="
                  activeGroup === group
                    ? 'text-white border-b-2 border-[#3C83F8]'
                    : 'text-gray-500 hover:text-gray-300'
                "
                @click="activeGroup = group"
              >
                <span>{{ tabGroupEmojis[group] }}</span>
                <span>{{ group }}</span>
              </button>
            </div>

            <!-- Zone principale scrollable -->
            <div class="flex-1 p-3 overflow-y-auto space-y-3">
              <!-- ── Formulaire de création (mode toggle) ── -->
              <template v-if="showCreateForm">
                <div class="flex items-center justify-between mb-1">
                  <p
                    class="text-xs font-semibold text-[#3C83F8] uppercase tracking-wider"
                  >
                    New asset — {{ activeGroup }}
                  </p>
                  <button
                    class="text-xs text-gray-500 hover:text-gray-300"
                    @click="showCreateForm = false"
                  >
                    ✕ Cancel
                  </button>
                </div>

                <!-- Supply form -->
                <template v-if="activeGroup === 'Supply'">
                  <div class="space-y-2">
                    <div>
                      <label class="text-xs text-gray-400 block mb-0.5"
                        >Type</label
                      >
                      <USelect
                        v-model="createSupplyForm.type"
                        :items="[
                          { label: '💨 Wind Turbine', value: 'wind_turbine' },
                          { label: '☀️ Solar Panel', value: 'solar_panel' },
                          { label: '☢️ Nuclear Plant', value: 'nuclear_plant' },
                        ]"
                        size="sm"
                        class="w-full"
                      />
                    </div>
                    <div>
                      <label class="text-xs text-gray-400 block mb-0.5"
                        >Name</label
                      >
                      <UInput
                        v-model="createSupplyForm.name"
                        size="sm"
                        placeholder="ex: Wind Farm Alpha"
                      />
                    </div>
                    <div>
                      <label class="text-xs text-gray-400 block mb-0.5"
                        >Capacity (MW)</label
                      >
                      <UInput
                        v-model="createSupplyForm.capacity_mw"
                        type="number"
                        size="sm"
                      />
                    </div>
                    <div>
                      <label class="text-xs text-gray-400 block mb-0.5"
                        >Efficiency (0-1)</label
                      >
                      <UInput
                        v-model="createSupplyForm.efficiency"
                        type="number"
                        step="0.01"
                        size="sm"
                      />
                    </div>
                  </div>
                </template>

                <!-- Demand form -->
                <template v-else-if="activeGroup === 'Demand'">
                  <div class="space-y-2">
                    <div>
                      <label class="text-xs text-gray-400 block mb-0.5"
                        >Type</label
                      >
                      <USelect
                        v-model="createDemandForm.type"
                        :items="[
                          { label: '🏠 House', value: 'house' },
                          { label: '🚗 E-Vehicle', value: 'electric_vehicle' },
                        ]"
                        size="sm"
                        class="w-full"
                      />
                    </div>
                    <div>
                      <label class="text-xs text-gray-400 block mb-0.5"
                        >Name</label
                      >
                      <UInput
                        v-model="createDemandForm.name"
                        size="sm"
                        placeholder="ex: Groningen Zone A"
                      />
                    </div>
                    <div>
                      <label class="text-xs text-gray-400 block mb-0.5"
                        >Load (MW)</label
                      >
                      <UInput
                        v-model="createDemandForm.load_mw"
                        type="number"
                        size="sm"
                      />
                    </div>
                  </div>
                </template>

                <!-- Network form -->
                <template v-else>
                  <div class="space-y-2">
                    <div>
                      <label class="text-xs text-gray-400 block mb-0.5"
                        >Type</label
                      >
                      <USelect
                        v-model="createNetworkForm.type"
                        :items="[
                          { label: '⚙️ Transformer', value: 'transformer' },
                          { label: '🔌 Cable', value: 'cable' },
                        ]"
                        size="sm"
                        class="w-full"
                      />
                    </div>
                    <div>
                      <label class="text-xs text-gray-400 block mb-0.5"
                        >Name</label
                      >
                      <UInput
                        v-model="createNetworkForm.name"
                        size="sm"
                        placeholder="ex: HV Transformer 01"
                      />
                    </div>
                    <div>
                      <label class="text-xs text-gray-400 block mb-0.5"
                        >Voltage (kV)</label
                      >
                      <UInput
                        v-model="createNetworkForm.voltage_kv"
                        type="number"
                        size="sm"
                      />
                    </div>
                    <div>
                      <label class="text-xs text-gray-400 block mb-0.5"
                        >Capacity (MVA)</label
                      >
                      <UInput
                        v-model="createNetworkForm.capacity_mva"
                        type="number"
                        size="sm"
                      />
                    </div>
                  </div>
                </template>

                <UButton
                  block
                  icon="i-heroicons-plus"
                  label="Create and add"
                  color="primary"
                  size="sm"
                  class="mt-2"
                  :loading="isSaving"
                  :disabled="isSaving || !referential.backendAvailable"
                  @click="handleCreate"
                />
              </template>

              <!-- ── Mode sélection (défaut) ── -->
              <template v-else>
                <!-- Dropdown sélection asset -->
                <div>
                  <div class="flex items-center justify-between mb-1.5">
                    <p class="text-xs text-gray-500 uppercase tracking-wider">
                      Add to simulation
                    </p>
                    <button
                      class="text-xs text-[#3C83F8] hover:text-blue-300 font-medium"
                      :disabled="!referential.backendAvailable"
                      @click="showCreateForm = true"
                    >
                      + Create
                    </button>
                  </div>
                  <USelectMenu
                    v-model="assetToAdd"
                    :items="availableForDropdown"
                    value-attribute="value"
                    searchable
                    search-placeholder="Search assets..."
                    placeholder="Select an asset..."
                    class="w-full"
                    :disabled="
                      !referential.backendAvailable ||
                      availableForDropdown.length === 0
                    "
                    @update:model-value="handleAddAsset"
                  >
                    <template #item="{ item }">
                      <div
                        class="flex items-center justify-between w-full gap-2"
                      >
                        <span class="flex-1 truncate">{{ item.label }}</span>
                        <button
                          class="text-gray-700 hover:text-gray-500 flex-shrink-0 rounded"
                          @click.stop.prevent="
                            deleteTarget = {
                              id: item.value as string,
                              name: (item as any).name ?? item.label,
                              group: activeGroup,
                            }
                          "
                        >
                          <UIcon name="i-heroicons-trash" class="w-3 h-3" />
                        </button>
                      </div>
                    </template>
                  </USelectMenu>
                  <p
                    v-if="
                      referential.backendAvailable &&
                      availableForDropdown.length === 0 &&
                      selectedAssetsList.length > 0
                    "
                    class="text-xs text-gray-600 mt-1 text-center"
                  >
                    All assets are selected
                  </p>
                  <p
                    v-else-if="
                      referential.backendAvailable &&
                      availableForDropdown.length === 0 &&
                      selectedAssetsList.length === 0
                    "
                    class="text-xs text-gray-600 mt-1 text-center"
                  >
                    No assets — create one with + Create
                  </p>
                </div>

                <!-- Liste des assets sélectionnés -->
                <div class="border-t border-[#1E293B] pt-3">
                  <p
                    class="text-xs text-gray-500 uppercase tracking-wider mb-2"
                  >
                    In simulation
                    <span
                      class="ml-1 px-1.5 py-0.5 bg-[#1E293B] rounded text-gray-300 font-mono"
                      >{{ selectedCount }}</span
                    >
                  </p>

                  <div
                    v-if="selectedAssetsList.length === 0"
                    class="text-xs text-gray-600 text-center py-4"
                  >
                    No assets selected
                  </div>

                  <div
                    v-for="asset in selectedAssetsList"
                    :key="asset.id"
                    class="rounded-lg bg-[#020617] border mb-2 overflow-hidden"
                    :class="
                      expandedAssetId === asset.id
                        ? 'border-[#3C83F8]/50'
                        : 'border-[#1E293B]'
                    "
                  >
                    <!-- Card header -->
                    <div
                      class="p-2.5 cursor-pointer select-none"
                      @click="toggleExpand(asset.id)"
                    >
                      <div class="flex items-start justify-between gap-1">
                        <div class="flex-1 min-w-0">
                          <div class="flex items-center gap-1 flex-wrap">
                            <p
                              class="text-xs font-semibold text-white truncate"
                            >
                              {{ typeEmoji(asset.type) }} {{ asset.name }}
                            </p>
                            <span
                              v-if="hasOverridesFor(asset.id)"
                              class="text-xs px-1 py-0.5 bg-amber-900/40 text-amber-400 rounded leading-none"
                              >Modified</span
                            >
                          </div>
                          <p class="text-xs text-gray-500 mt-0.5 truncate">
                            {{ assetSummary(asset) }}
                          </p>
                        </div>
                        <span
                          class="text-gray-600 text-xs flex-shrink-0 mt-0.5"
                          >{{ expandedAssetId === asset.id ? "▲" : "▼" }}</span
                        >
                        <button
                          class="text-red-400 hover:text-red-300 text-xs flex-shrink-0 mt-0.5"
                          @click.stop="removeFromSelection(asset.id)"
                        >
                          ✕
                        </button>
                      </div>
                    </div>

                    <!-- Expandable override panel -->
                    <div
                      v-if="expandedAssetId === asset.id"
                      class="border-t border-[#1E293B] p-2.5 space-y-2 bg-[#0a111e]"
                    >
                      <p
                        class="text-xs text-gray-500 uppercase tracking-wider mb-1"
                      >
                        Parameters
                      </p>

                      <!-- Supply fields -->
                      <template
                        v-if="
                          activeGroup === 'Supply' && 'capacity_mw' in asset
                        "
                      >
                        <div>
                          <label class="text-xs text-gray-400 block mb-0.5"
                            >Capacity (MW)</label
                          >
                          <UInput
                            :model-value="
                              getOverrideValue(
                                asset.id,
                                'capacity_mw',
                                (asset as Supply).capacity_mw,
                              )
                            "
                            type="number"
                            size="xs"
                            @update:model-value="
                              setOverrideValue(asset.id, 'capacity_mw', $event)
                            "
                          />
                        </div>
                        <div>
                          <label class="text-xs text-gray-400 block mb-0.5"
                            >Efficiency (0-1)</label
                          >
                          <UInput
                            :model-value="
                              getOverrideValue(
                                asset.id,
                                'efficiency',
                                (asset as Supply).efficiency,
                              )
                            "
                            type="number"
                            step="0.01"
                            size="xs"
                            @update:model-value="
                              setOverrideValue(asset.id, 'efficiency', $event)
                            "
                          />
                        </div>
                      </template>

                      <!-- Demand fields -->
                      <template
                        v-else-if="
                          activeGroup === 'Demand' && 'load_mw' in asset
                        "
                      >
                        <div>
                          <label class="text-xs text-gray-400 block mb-0.5"
                            >Load (MW)</label
                          >
                          <UInput
                            :model-value="
                              getOverrideValue(
                                asset.id,
                                'load_mw',
                                (asset as Demand).load_mw,
                              )
                            "
                            type="number"
                            size="xs"
                            @update:model-value="
                              setOverrideValue(asset.id, 'load_mw', $event)
                            "
                          />
                        </div>
                      </template>

                      <!-- Network fields -->
                      <template
                        v-else-if="
                          activeGroup === 'Network' && 'capacity_mva' in asset
                        "
                      >
                        <div>
                          <label class="text-xs text-gray-400 block mb-0.5"
                            >Capacity (MVA)</label
                          >
                          <UInput
                            :model-value="
                              getOverrideValue(
                                asset.id,
                                'capacity_mva',
                                (asset as NetworkComponent).capacity_mva,
                              )
                            "
                            type="number"
                            size="xs"
                            @update:model-value="
                              setOverrideValue(asset.id, 'capacity_mva', $event)
                            "
                          />
                        </div>
                      </template>

                      <button
                        v-if="hasOverridesFor(asset.id)"
                        class="text-xs text-gray-500 hover:text-gray-300 mt-1"
                        @click="clearOverridesFor(asset.id)"
                      >
                        ↺ Reset
                      </button>
                    </div>
                  </div>
                </div>
              </template>

              <!-- Spinner chargement -->
              <div
                v-if="referential.referentialLoading"
                class="flex justify-center pt-2"
              >
                <div
                  class="animate-spin h-5 w-5 border-t-2 border-[#3C83F8] rounded-full"
                />
              </div>
            </div>

            <!-- Boutons bas de sidebar -->
            <div class="border-t border-[#1E293B] p-3 flex flex-col gap-2">
              <div class="text-xs text-gray-600 text-center">
                {{ store.selectedSupplyIds.length }}S ·
                {{ store.selectedDemandIds.length }}D ·
                {{ store.selectedNetworkIds.length }}N sélectionnés
              </div>
              <UButton
                block
                icon="i-heroicons-arrow-path"
                label="Reload from API"
                color="neutral"
                variant="outline"
                size="sm"
                :loading="referential.referentialLoading"
                @click="referential.loadReferential()"
              />
            </div>
          </div>
        </aside>
      </Transition>

      <!-- Zone centrale -->
      <main class="flex-1 overflow-y-auto p-6">
        <NuxtPage />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  fetchScenarioExport,
  type Demand,
  type NetworkComponent,
  type ScenarioExport,
  type Supply,
} from "~/composables/api";
import { useHistoryStore } from "~/stores/history";
import { useReferentialStore } from "~/stores/referential";
import { useSimulationStore } from "~/stores/simulation";

const store = useSimulationStore();
const referential = useReferentialStore();
const history = useHistoryStore();
const toast = useToast();

const handleHeaderRename = async () => {
  const id = history.selectedSimulationId;
  const name = store.scenarioName.trim();
  if (!id || !name) return;
  try {
    await history.renameEntry(id, name);
    toast.add({ title: "Scenario renamed", color: "success" });
  } catch {
    toast.add({ title: "Rename failed", color: "error" });
  }
};

// ─── Play handler ─────────────────────────────────────────────────────────────

const handlePlay = async () => {
  if (!referential.backendAvailable) {
    toast.add({
      title: "Backend unavailable",
      description: "Start the API server",
      color: "warning",
    });
    return;
  }
  if (
    store.selectedSupplyIds.length === 0 ||
    store.selectedDemandIds.length === 0
  ) {
    toast.add({
      title: "Incomplete selection",
      description: "Select at least one supply and one demand in the sidebar",
      color: "warning",
    });
    return;
  }
  try {
    const result = await store.runFullSimulation();
    if (result.status === "error") {
      toast.add({
        title: "Infeasible simulation",
        description: "PyPSA did not find an optimal solution",
        color: "error",
      });
    } else {
      toast.add({
        title: "Simulation complete",
        description: `Status: ${result.status}`,
        color: "success",
      });
    }
  } catch {
    toast.add({
      title: "Simulation error",
      description: store.error ?? "Unknown error",
      color: "error",
    });
  }
};

// ─── Sidebar state ────────────────────────────────────────────────────────────

const sidebarOpen = ref(true);
const activeGroup = ref("Supply");
const assetToAdd = ref("");
const showCreateForm = ref(false);
const isSaving = ref(false);
const expandedAssetId = ref<string | null>(null);

// ─── Export / Import ──────────────────────────────────────────────────────────

const fileInput = ref<HTMLInputElement | null>(null);
const showSolverHelpModal = ref(false);

const solverOptions = [
  {
    label: "HiGHS",
    value: "highs",
    description:
      "Minimizes total operating cost — fast LP, open-source (default)",
    speed: "Fast",
    license: "Open-source",
    bestFor: "Default choice for most LP economic dispatch simulations",
  },
  {
    label: "GLPK",
    value: "glpk",
    description:
      "Minimizes total cost — reliable LP/MIP but slower, open-source",
    speed: "Slow",
    license: "Open-source",
    bestFor: "Simple runs and compatibility checks",
  },
  {
    label: "CBC",
    value: "cbc",
    description:
      "Optimizes ON/OFF unit commitment decisions — MIP open-source (COIN-OR)",
    speed: "Medium",
    license: "Open-source",
    bestFor: "Mixed-integer problems with binary commitments",
  },
  {
    label: "SCIP",
    value: "scip",
    description:
      "Solves complex MIP problems with constraints — academic solver",
    speed: "Medium",
    license: "Academic",
    bestFor: "Complex MIP formulations in research contexts",
  },
  {
    label: "Gurobi",
    value: "gurobi",
    description: "Minimizes cost or emissions ultra-fast — LP/MIP commercial",
    speed: "Very fast",
    license: "Commercial",
    bestFor: "Large-scale industrial optimization with strict runtime targets",
  },
  {
    label: "CPLEX",
    value: "cplex",
    description: "Industrial-grade LP/MIP optimization — IBM, commercial",
    speed: "Very fast",
    license: "Commercial",
    bestFor: "Enterprise-grade robust optimization workloads",
  },
  {
    label: "Xpress",
    value: "xpress",
    description: "Large-scale LP/MIP optimization — FICO, commercial",
    speed: "Very fast",
    license: "Commercial",
    bestFor: "High-performance LP/MIP on large utility-scale systems",
  },
] as const;

const solverSelectItems = solverOptions.map(({ label, value }) => ({
  label,
  value,
}));

const selectedSolverTitle = computed(() => {
  const selected = solverOptions.find(
    (option) => option.value === store.solver,
  );
  return selected ? `${selected.label} - ${selected.description}` : "Solver";
});

const selectedSolverLabel = computed(() => {
  const selected = solverOptions.find(
    (option) => option.value === store.solver,
  );
  return selected?.label ?? "Unknown";
});

const handleExport = async () => {
  const id = history.selectedSimulationId ?? history.currentResult?.id;
  if (!id) return;
  try {
    const scenario = await fetchScenarioExport(id);
    const name = history.currentResult?.name ?? id;
    const filename = `scenario-${name}-${new Date().toISOString().slice(0, 10)}.json`;
    const blob = new Blob([JSON.stringify(scenario, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  } catch {
    toast.add({ title: "Export error", color: "error" });
  }
};

const handleImport = (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      const scenario = JSON.parse(e.target?.result as string) as ScenarioExport;
      store.loadFromScenario(scenario, file.name.replace(".json", ""));
      toast.add({ title: "Scenario loaded", color: "success" });
    } catch {
      toast.add({ title: "Invalid file", color: "error" });
    } finally {
      if (fileInput.value) fileInput.value.value = "";
    }
  };
  reader.readAsText(file);
};

// ─── Delete asset ─────────────────────────────────────────────────────────────

const deleteTarget = ref<{ id: string; name: string; group: string } | null>(
  null,
);
const isDeleting = ref(false);

const showDeleteModal = computed({
  get: () => deleteTarget.value !== null,
  set: (val: boolean) => {
    if (!val) deleteTarget.value = null;
  },
});

const handleDeleteAsset = async () => {
  if (!deleteTarget.value) return;
  isDeleting.value = true;
  try {
    const { id, group } = deleteTarget.value;
    if (group === "Supply") await store.removeSupply(id);
    else if (group === "Demand") await store.removeDemand(id);
    else await store.removeNetworkComponent(id);
    toast.add({ title: "Asset deleted", color: "success" });
    deleteTarget.value = null;
  } catch (e: unknown) {
    toast.add({
      title: "Deletion error",
      description: e instanceof Error ? e.message : "Unknown error",
      color: "error",
    });
  } finally {
    isDeleting.value = false;
  }
};

const tabGroups = ["Supply", "Network", "Demand"] as const;
const tabGroupEmojis: Record<string, string> = {
  Supply: "⚡",
  Network: "🔌",
  Demand: "🏠",
};

// ─── Helpers d'affichage ──────────────────────────────────────────────────────

function typeEmoji(type: string): string {
  const map: Record<string, string> = {
    wind_turbine: "💨",
    solar_panel: "☀️",
    nuclear_plant: "☢️",
    house: "🏠",
    electric_vehicle: "🚗",
    cable: "🔌",
    transformer: "⚙️",
  };
  return map[type] ?? "❓";
}

function assetSummary(asset: Supply | Demand | NetworkComponent): string {
  if ("capacity_mw" in asset)
    return `${asset.capacity_mw} MW · eff ${asset.efficiency}`;
  if ("load_mw" in asset) return `${asset.load_mw} MW`;
  if ("voltage_kv" in asset)
    return `${asset.voltage_kv} kV · ${asset.capacity_mva} MVA`;
  return "";
}

// ─── Computed sélection / disponible ─────────────────────────────────────────

const availableForDropdown = computed(() => {
  if (activeGroup.value === "Supply") {
    return referential.availableSupplies
      .filter((s: Supply) => !store.selectedSupplyIds.includes(s.id))
      .map((s: Supply) => ({
        label: `${typeEmoji(s.type)} ${s.name}`,
        value: s.id,
        name: s.name,
      }));
  }
  if (activeGroup.value === "Demand") {
    return referential.availableDemands
      .filter((d: Demand) => !store.selectedDemandIds.includes(d.id))
      .map((d: Demand) => ({
        label: `${typeEmoji(d.type)} ${d.name}`,
        value: d.id,
        name: d.name,
      }));
  }
  if (activeGroup.value === "Network") {
    return referential.availableNetwork
      .filter((n: NetworkComponent) => !store.selectedNetworkIds.includes(n.id))
      .map((n: NetworkComponent) => ({
        label: `${typeEmoji(n.type)} ${n.name}`,
        value: n.id,
        name: n.name,
      }));
  }
  return [];
});

const selectedAssetsList = computed<Array<Supply | Demand | NetworkComponent>>(
  () => {
    if (activeGroup.value === "Supply") return store.selectedSupplies;
    if (activeGroup.value === "Demand") return store.selectedDemands;
    if (activeGroup.value === "Network") return store.selectedNetwork;
    return [];
  },
);

const selectedCount = computed(() => selectedAssetsList.value.length);

// ─── Actions sélection ────────────────────────────────────────────────────────

const handleAddAsset = (val: string | { value: string } | null) => {
  const id = val && typeof val === "object" ? val.value : val;
  if (!id) return;
  if (activeGroup.value === "Supply") store.addSupplyToSelection(id);
  else if (activeGroup.value === "Demand") store.addDemandToSelection(id);
  else store.addNetworkToSelection(id);
  nextTick(() => {
    assetToAdd.value = "";
  });
};

const removeFromSelection = (id: string) => {
  if (expandedAssetId.value === id) expandedAssetId.value = null;
  if (activeGroup.value === "Supply") store.removeSupplyFromSelection(id);
  else if (activeGroup.value === "Demand") store.removeDemandFromSelection(id);
  else store.removeNetworkFromSelection(id);
};

// Réinitialiser dropdown, formulaire et expansion au changement d'onglet
watch(activeGroup, () => {
  assetToAdd.value = "";
  showCreateForm.value = false;
  expandedAssetId.value = null;
});

// ─── Override helpers ─────────────────────────────────────────────────────────

function currentGroupType(): "supply" | "demand" | "network" {
  if (activeGroup.value === "Supply") return "supply";
  if (activeGroup.value === "Demand") return "demand";
  return "network";
}

function toggleExpand(id: string) {
  expandedAssetId.value = expandedAssetId.value === id ? null : id;
}

function hasOverridesFor(id: string): boolean {
  return store.hasOverrides(currentGroupType(), id);
}

function getOverrideValue(
  id: string,
  field: string,
  defaultVal: number,
): number {
  const assetOverrides = store.getOverrides(currentGroupType(), id);
  return field in assetOverrides ? assetOverrides[field] : defaultVal;
}

function setOverrideValue(
  id: string,
  field: string,
  rawValue: string | number,
) {
  const value = typeof rawValue === "string" ? parseFloat(rawValue) : rawValue;
  if (!isNaN(value)) store.setOverride(currentGroupType(), id, field, value);
}

function clearOverridesFor(id: string) {
  store.clearOverrides(currentGroupType(), id);
}

// ─── Formulaires de création ──────────────────────────────────────────────────

const createSupplyForm = reactive({
  type: "wind_turbine" as "wind_turbine" | "solar_panel" | "nuclear_plant",
  name: "",
  capacity_mw: 500,
  efficiency: 0.42,
  status: "active" as const,
  unit: "MW",
  description: "",
});

const createDemandForm = reactive({
  type: "house" as "house" | "electric_vehicle",
  name: "",
  load_mw: 120,
  status: "active" as const,
  unit: "MW",
  description: "",
});

const createNetworkForm = reactive({
  type: "transformer" as "transformer" | "cable",
  name: "",
  voltage_kv: 400,
  capacity_mva: 500,
  status: "active" as const,
  unit: "MVA",
  description: "",
});

const handleCreate = async () => {
  isSaving.value = true;
  try {
    if (activeGroup.value === "Supply") {
      const created = await referential.addSupply({ ...createSupplyForm });
      store.addSupplyToSelection(created.id);
      createSupplyForm.name = "";
    } else if (activeGroup.value === "Demand") {
      const created = await referential.addDemand({ ...createDemandForm });
      store.addDemandToSelection(created.id);
      createDemandForm.name = "";
    } else {
      const created = await referential.addNetworkComponent({
        ...createNetworkForm,
        losses_kw: null,
        voltage_hv_kv: null,
        voltage_lv_kv: null,
        length_km: null,
        resistance_ohm_per_km: null,
        reactance_ohm_per_km: null,
      });
      store.addNetworkToSelection(created.id);
      createNetworkForm.name = "";
    }
    toast.add({
      title: "Asset created and added to simulation",
      color: "success",
    });
    showCreateForm.value = false;
  } catch (e: unknown) {
    toast.add({
      title: "Error",
      description: e instanceof Error ? e.message : "Unknown error",
      color: "error",
    });
  } finally {
    isSaving.value = false;
  }
};
</script>

<style scoped>
.sidebar-enter-active,
.sidebar-leave-active {
  transition:
    width 0.4s ease,
    opacity 0.2s ease;
  width: 240px;
}
.sidebar-enter-from,
.sidebar-leave-to {
  width: 0;
  opacity: 0;
}
</style>
