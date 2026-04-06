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
          <span class="font-semibold text-white">{{ deleteTarget?.name }}</span>?
          This action cannot be undone.
        </p>
      </template>
      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton label="Cancel" color="neutral" variant="ghost" @click="deleteTarget = null" />
          <UButton label="Delete" color="error" :loading="isDeleting" @click="handleDeleteAsset" />
        </div>
      </template>
    </UModal>

    <!-- Save choice modal: Replace or New -->
    <UModal v-model:open="showSaveChoiceModal">
      <template #header>
        <h3 class="text-base font-semibold text-white">Save simulation</h3>
      </template>
      <template #body>
        <p class="text-sm text-gray-300">
          The parameters have changed since the last simulation was saved.
          Do you want to <span class="font-semibold text-white">replace</span> the existing simulation
          or save as a <span class="font-semibold text-white">new one</span>?
        </p>
      </template>
      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton label="Cancel" color="neutral" variant="ghost" @click="showSaveChoiceModal = false" />
          <UButton label="New simulation" color="neutral" variant="outline" :loading="store.isSaving" @click="handleSaveNew" />
          <UButton label="Replace" color="primary" :loading="store.isSaving" @click="handleSaveReplace" />
        </div>
      </template>
    </UModal>

    <!-- Solver helper modal -->
    <UModal v-model:open="showSolverHelpModal">
      <template #header>
        <div class="flex items-center justify-between gap-3 w-full">
          <div>
            <h3 class="text-base font-semibold text-white">Solver helper</h3>
            <p class="text-xs text-gray-400 mt-0.5">Quick guide to choose the best optimization solver.</p>
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
            :class="solver.value === store.solver ? 'ring-1 ring-[#3C83F8]/60' : ''"
          >
            <div class="flex items-center justify-between gap-3 mb-1">
              <p class="text-sm font-semibold text-white">{{ solver.label }}</p>
              <div class="flex items-center gap-1.5">
                <span v-if="isSolverUnavailable(solver.value)" class="text-[11px] px-1.5 py-0.5 rounded bg-red-900/30 text-red-300">Unavailable</span>
                <span class="text-[11px] px-1.5 py-0.5 rounded bg-[#1E293B] text-slate-300">{{ solver.license }}</span>
                <span class="text-[11px] px-1.5 py-0.5 rounded bg-[#1E293B] text-slate-300">{{ solver.speed }}</span>
              </div>
            </div>
            <p class="text-xs text-slate-300">{{ solver.description }}</p>
            <p class="text-xs text-gray-400 mt-1.5">Best for: {{ solver.bestFor }}</p>
            <p v-if="isSolverUnavailable(solver.value)" class="text-xs text-red-300/90 mt-1">
              {{ solverUnavailableReason(solver.value) }}
            </p>
          </div>
        </div>
      </template>
      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton label="Close" color="neutral" variant="ghost" @click="showSolverHelpModal = false" />
        </div>
      </template>
    </UModal>

    <!-- ── Header ─────────────────────────────────────────────────────────────── -->
    <header class="bg-[#0F172A] border-b border-[#1E293B] shrink-0">

      <!-- Row 1: Logo + title + status + primary actions -->
      <div class="flex items-center gap-2 px-4 h-14">
        <UButton
          variant="ghost"
          icon="i-heroicons-bars-3"
          color="neutral"
          @click="sidebarOpen = !sidebarOpen"
        />

        <img src="/logo.png" alt="EnergyDash" class="h-8 w-auto">

        <span class="font-semibold text-base text-white hidden sm:block">
          Energy Network Simulator 2026
        </span>

        <!-- Backend status badge -->
        <span
          class="text-xs px-2 py-1 rounded-full ml-2"
          :class="referential.backendAvailable === true
            ? 'bg-emerald-900/40 text-emerald-400'
            : referential.backendAvailable === false
              ? 'bg-red-900/40 text-red-400'
              : 'bg-gray-800 text-gray-500'"
        >
          {{ referential.backendAvailable === true ? '● Connected' : referential.backendAvailable === false ? '● Offline' : '● …' }}
        </span>

        <div class="flex-1" />

        <!-- Weather station indicator -->
        <div
          class="hidden sm:flex items-center gap-1 text-xs text-gray-500 border border-[#1E293B] rounded px-2 h-6 shrink-0"
          title="Weather data source: KNMI station 06280 — Groningen Eelde. Covers Jan 2025 → Dec 2025."
        >
          <UIcon name="i-heroicons-map-pin" class="w-3 h-3 text-gray-600" />
          <span>KNMI · Groningen Eelde</span>
        </div>

        <!-- Save button — only active in live mode -->
        <UButton
          icon="i-heroicons-cloud-arrow-up"
          color="primary"
          :label="store.isSaving ? 'Saving…' : 'Save'"
          :loading="store.isSaving"
          :disabled="store.isSaving || !store.isLiveMode || !store.hasMinimumAssets || !referential.backendAvailable || store.paramsMatchSaved"
          size="sm"
          @click="handleSave"
        />

        <!-- Export button -->
        <UButton
          icon="i-heroicons-arrow-down-tray"
          label="Export"
          size="sm"
          color="neutral"
          variant="outline"
          :disabled="!history.currentResult && !history.selectedSimulationId"
          @click="handleExport"
        />
      </div>

      <!-- Row 2: Hours + Solver + Scenario name + Import + Live indicator -->
      <div class="flex items-center gap-3 px-4 h-10 border-t border-[#1E293B] bg-[#020617]/40">

        <!-- Duration mode toggle -->
        <div class="flex items-center gap-0 rounded border border-[#334155] overflow-hidden shrink-0">
          <button
            class="px-2.5 h-6 text-xs transition-colors"
            :class="dateMode === 'hours' ? 'bg-[#1E293B] text-white' : 'bg-transparent text-gray-500 hover:text-gray-300'"
            @click="setDateMode('hours')"
          >Hours</button>
          <button
            class="px-2.5 h-6 text-xs transition-colors border-l border-[#334155]"
            :class="dateMode === 'dates' ? 'bg-[#1E293B] text-white' : 'bg-transparent text-gray-500 hover:text-gray-300'"
            @click="setDateMode('dates')"
          >Date range</button>
        </div>

        <!-- Hours selector -->
        <div v-if="dateMode === 'hours'" class="flex items-center gap-1.5">
          <USelect
            v-model="store.snapshotHours"
            :items="[
              { label: '1 h', value: 1 },
              { label: '24 h', value: 24 },
              { label: '168 h', value: 168 },
              { label: '8760 h', value: 8760 },
            ]"
            class="w-24"
            size="xs"
          />
        </div>

        <!-- Date range picker -->
        <div v-else class="flex items-center gap-0 rounded border border-[#334155] overflow-hidden">
          <input
            v-model="store.startDate"
            type="date"
            min="2025-01-01"
            max="2025-12-31"
            class="h-6 px-1.5 text-xs bg-[#0F172A] text-white focus:outline-none focus:bg-[#0F172A]/80 w-32 border-0"
          />
          <span class="text-xs text-gray-600 px-1 shrink-0 border-x border-[#334155]">→</span>
          <input
            v-model="store.endDate"
            type="date"
            min="2025-01-01"
            max="2025-12-31"
            class="h-6 px-1.5 text-xs bg-[#0F172A] text-white focus:outline-none focus:bg-[#0F172A]/80 w-32 border-0"
          />
          <span
            v-if="store.startDate && store.endDate"
            class="text-xs text-emerald-400 font-mono px-1.5 border-l border-[#334155] shrink-0"
          >{{ store.snapshotHours }}h</span>
        </div>

        <!-- Solver selector with availability -->
        <div class="flex items-center gap-1.5" :title="selectedSolverTitle">
          <label class="text-xs text-gray-500">Solver</label>
          <USelect
            v-model="store.solver"
            :items="solverSelectItems"
            :loading="solverAvailabilityLoading"
            class="w-36"
            size="xs"
          />
          <UButton
            icon="i-heroicons-question-mark-circle"
            size="xs"
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
            size="xs"
            class="w-44"
          />
          <UButton
            icon="i-heroicons-pencil-square"
            size="xs"
            color="neutral"
            variant="ghost"
            title="Rename selected scenario"
            :disabled="!history.selectedSimulationId"
            @click="handleHeaderRename"
          />
        </div>

        <!-- Import -->
        <input ref="fileInput" type="file" accept=".json" class="hidden" @change="handleImport" />
        <UButton
          icon="i-heroicons-arrow-up-tray"
          label="Import"
          size="xs"
          color="neutral"
          variant="outline"
          @click="fileInput?.click()"
        />

        <div class="flex-1" />

        <!-- Live indicator (live mode) / Saved sim badge (history mode) -->
        <div v-if="store.isLiveMode" class="flex items-center gap-1.5 select-none">
          <span class="relative flex h-2 w-2">
            <span
              v-if="store.isLiveRunning"
              class="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"
            />
            <span
              class="relative inline-flex rounded-full h-2 w-2 transition-colors duration-300"
              :class="store.isLiveRunning
                ? 'bg-amber-400'
                : store.hasMinimumAssets && referential.backendAvailable
                  ? 'bg-emerald-400'
                  : 'bg-gray-600'"
            />
          </span>
          <span
            class="text-xs transition-colors duration-300"
            :class="store.isLiveRunning
              ? 'text-amber-400'
              : store.hasMinimumAssets && referential.backendAvailable
                ? 'text-emerald-400'
                : 'text-gray-600'"
          >
            {{ store.isLiveRunning ? 'Running…' : store.hasMinimumAssets && referential.backendAvailable ? 'Live' : 'Idle' }}
          </span>
        </div>
        <div v-else class="flex items-center gap-1.5 text-xs text-gray-500 select-none">
          <UIcon name="i-heroicons-archive-box" class="w-3.5 h-3.5" />
          <span>Saved sim</span>
        </div>
      </div>
    </header>

    <!-- ── Body ───────────────────────────────────────────────────────────────── -->
    <div class="flex flex-1 overflow-hidden">

      <!-- ── Sidebar ──────────────────────────────────────────────────────────── -->
      <Transition name="sidebar">
        <aside
          v-if="sidebarOpen"
          class="w-60 bg-[#0F172A] border-r border-[#1E293B] flex flex-col shrink-0 overflow-hidden"
        >
          <!-- Scrollable section list -->
          <div class="flex-1 overflow-y-auto">

            <!-- ── Section: Supply ── -->
            <div class="border-b border-[#1E293B]">
              <button
                class="w-full flex items-center gap-2 px-3 py-2.5 text-sm font-medium hover:bg-[#1E293B]/60 transition-colors cursor-pointer"
                :class="activeGroup === 'Supply' ? 'text-[#3C83F8]' : 'text-gray-300'"
                @click="setActiveGroup('Supply')"
              >
                <UIcon name="i-heroicons-bolt" class="w-3.5 h-3.5 text-amber-400 shrink-0" />
                <span class="uppercase tracking-wider text-xs font-bold flex-1 text-left">Supply</span>
                <span
                  v-if="store.selectedSupplyIds.length"
                  class="text-xs px-1.5 py-0.5 rounded bg-[#1E293B] text-gray-300 font-mono leading-none"
                >{{ store.selectedSupplyIds.length }}</span>
                <UIcon
                  :name="activeGroup === 'Supply' ? 'i-heroicons-chevron-up' : 'i-heroicons-chevron-right'"
                  class="w-3 h-3 text-gray-500 shrink-0"
                />
              </button>

              <div v-if="activeGroup === 'Supply'" class="px-3 pb-3 space-y-3">
                <template v-if="showCreateForm">
                  <div class="flex items-center justify-between mt-2 mb-1">
                    <p class="text-xs font-semibold text-[#3C83F8] uppercase tracking-wider">New Supply asset</p>
                    <button class="text-xs text-gray-500 hover:text-gray-300" @click="showCreateForm = false">✕ Cancel</button>
                  </div>
                  <div class="space-y-2">
                    <div>
                      <label class="text-xs text-gray-400 block mb-0.5">Type</label>
                      <USelect
                        v-model="createSupplyForm.type"
                        :items="[
                          { label: 'Wind Turbine', value: 'wind_turbine' },
                          { label: 'Solar Panel', value: 'solar_panel' },
                          { label: 'Nuclear Plant', value: 'nuclear_plant' },
                        ]"
                        size="sm" class="w-full"
                      />
                    </div>
                    <div>
                      <label class="text-xs text-gray-400 block mb-0.5">Name</label>
                      <UInput v-model="createSupplyForm.name" size="sm" placeholder="e.g. Wind Farm Alpha" />
                    </div>
                    <div>
                      <label class="text-xs text-gray-400 block mb-0.5">Capacity (MW)</label>
                      <UInput v-model="createSupplyForm.capacity_mw" type="number" size="sm" />
                    </div>
                    <div>
                      <label class="text-xs text-gray-400 block mb-0.5">Efficiency (0–1)</label>
                      <UInput v-model="createSupplyForm.efficiency" type="number" step="0.01" size="sm" />
                    </div>
                  </div>
                  <UButton
                    block icon="i-heroicons-plus" label="Create and add"
                    color="primary" size="sm"
                    :loading="isSaving" :disabled="isSaving || !referential.backendAvailable"
                    @click="handleCreate"
                  />
                </template>

                <template v-else>
                  <div class="mt-2">
                    <div class="flex items-center justify-between mb-1.5">
                      <p class="text-xs text-gray-500 uppercase tracking-wider">Add to simulation</p>
                      <button
                        class="text-xs text-[#3C83F8] hover:text-blue-300 font-medium"
                        :disabled="!referential.backendAvailable"
                        @click="showCreateForm = true"
                      >+ New</button>
                    </div>
                    <USelectMenu
                      v-model="assetToAdd"
                      :items="availableForDropdown"
                      value-attribute="value"
                      searchable
                      search-placeholder="Search assets..."
                      placeholder="Select an asset..."
                      class="w-full"
                      :disabled="!referential.backendAvailable || availableForDropdown.length === 0"
                      @update:model-value="handleAddAsset"
                    >
                      <template #item="{ item }">
                        <div class="flex items-center justify-between w-full gap-2">
                          <span class="flex-1 truncate">{{ item.label }}</span>
                          <button
                            class="text-gray-700 hover:text-gray-500 flex-shrink-0 rounded"
                            @click.stop.prevent="deleteTarget = { id: item.value as string, name: (item as any).name ?? item.label, group: activeGroup }"
                          >
                            <UIcon name="i-heroicons-trash" class="w-3 h-3" />
                          </button>
                        </div>
                      </template>
                    </USelectMenu>
                    <p
                      v-if="referential.backendAvailable && availableForDropdown.length === 0 && selectedAssetsList.length > 0"
                      class="text-xs text-gray-600 mt-1 text-center"
                    >All assets are selected</p>
                    <p
                      v-else-if="referential.backendAvailable && availableForDropdown.length === 0 && selectedAssetsList.length === 0"
                      class="text-xs text-gray-600 mt-1 text-center"
                    >No assets — create one with + New</p>
                  </div>

                  <div v-if="selectedAssetsList.length" class="border-t border-[#1E293B] pt-2 space-y-1.5">
                    <div
                      v-for="asset in selectedAssetsList"
                      :key="asset.id"
                      class="rounded-lg bg-[#020617] border overflow-hidden"
                      :class="expandedAssetId === asset.id ? 'border-[#3C83F8]/50' : 'border-[#1E293B]'"
                    >
                      <div class="p-2 cursor-pointer select-none" @click="toggleExpand(asset.id)">
                        <div class="flex items-start justify-between gap-1">
                          <div class="flex-1 min-w-0">
                            <div class="flex items-center gap-1.5 flex-wrap">
                              <UiAssetTypeIcon :type="asset.type" size="xs" />
                              <p class="text-xs font-semibold text-white truncate">{{ asset.name }}</p>
                              <span v-if="hasOverridesFor(asset.id)" class="text-xs px-1 py-0.5 bg-amber-900/40 text-amber-400 rounded leading-none">Edited</span>
                            </div>
                            <p class="text-xs text-gray-500 mt-0.5 truncate">{{ assetSummary(asset) }}</p>
                          </div>
                          <UIcon
                            :name="expandedAssetId === asset.id ? 'i-heroicons-chevron-up' : 'i-heroicons-chevron-down'"
                            class="w-3 h-3 text-gray-600 shrink-0 mt-0.5"
                          />
                          <button class="text-red-400 hover:text-red-300 shrink-0 mt-0.5" @click.stop="removeFromSelection(asset.id)">
                            <UIcon name="i-heroicons-x-mark" class="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                      <div v-if="expandedAssetId === asset.id" class="border-t border-[#1E293B] p-2 space-y-2 bg-[#0a111e]">
                        <p class="text-xs text-gray-500 uppercase tracking-wider mb-1">Parameters</p>
                        <template v-if="'capacity_mw' in asset">
                          <div>
                            <label class="text-xs text-gray-400 block mb-0.5">Capacity (MW)</label>
                            <UInput
                              :model-value="getOverrideValue(asset.id, 'capacity_mw', (asset as Supply).capacity_mw)"
                              type="number" size="xs"
                              @update:model-value="setOverrideValue(asset.id, 'capacity_mw', $event)"
                            />
                          </div>
                          <div>
                            <label class="text-xs text-gray-400 block mb-0.5">Efficiency (0–1)</label>
                            <UInput
                              :model-value="getOverrideValue(asset.id, 'efficiency', (asset as Supply).efficiency)"
                              type="number" step="0.01" size="xs"
                              @update:model-value="setOverrideValue(asset.id, 'efficiency', $event)"
                            />
                          </div>
                        </template>
                        <button v-if="hasOverridesFor(asset.id)" class="text-xs text-gray-500 hover:text-gray-300 mt-1" @click="clearOverridesFor(asset.id)">
                          ↺ Reset
                        </button>
                      </div>
                    </div>
                  </div>
                  <p v-else class="text-xs text-gray-600 text-center py-2">No supply selected</p>
                </template>
              </div>
            </div>

            <!-- ── Section: Demand ── -->
            <div class="border-b border-[#1E293B]">
              <button
                class="w-full flex items-center gap-2 px-3 py-2.5 text-sm font-medium hover:bg-[#1E293B]/60 transition-colors cursor-pointer"
                :class="activeGroup === 'Demand' ? 'text-[#3C83F8]' : 'text-gray-300'"
                @click="setActiveGroup('Demand')"
              >
                <UIcon name="i-heroicons-home" class="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span class="uppercase tracking-wider text-xs font-bold flex-1 text-left">Demand</span>
                <span
                  v-if="store.selectedDemandIds.length"
                  class="text-xs px-1.5 py-0.5 rounded bg-[#1E293B] text-gray-300 font-mono leading-none"
                >{{ store.selectedDemandIds.length }}</span>
                <UIcon
                  :name="activeGroup === 'Demand' ? 'i-heroicons-chevron-up' : 'i-heroicons-chevron-right'"
                  class="w-3 h-3 text-gray-500 shrink-0"
                />
              </button>

              <div v-if="activeGroup === 'Demand'" class="px-3 pb-3 space-y-3">
                <template v-if="showCreateForm">
                  <div class="flex items-center justify-between mt-2 mb-1">
                    <p class="text-xs font-semibold text-[#3C83F8] uppercase tracking-wider">New Demand asset</p>
                    <button class="text-xs text-gray-500 hover:text-gray-300" @click="showCreateForm = false">✕ Cancel</button>
                  </div>
                  <div class="space-y-2">
                    <div>
                      <label class="text-xs text-gray-400 block mb-0.5">Type</label>
                      <USelect
                        v-model="createDemandForm.type"
                        :items="[
                          { label: 'House', value: 'house' },
                          { label: 'Electric Vehicle', value: 'electric_vehicle' },
                        ]"
                        size="sm" class="w-full"
                      />
                    </div>
                    <div>
                      <label class="text-xs text-gray-400 block mb-0.5">Name</label>
                      <UInput v-model="createDemandForm.name" size="sm" placeholder="e.g. Groningen Zone A" />
                    </div>
                    <div>
                      <label class="text-xs text-gray-400 block mb-0.5">Load (MW)</label>
                      <UInput v-model="createDemandForm.load_mw" type="number" size="sm" />
                    </div>
                  </div>
                  <UButton
                    block icon="i-heroicons-plus" label="Create and add"
                    color="primary" size="sm"
                    :loading="isSaving" :disabled="isSaving || !referential.backendAvailable"
                    @click="handleCreate"
                  />
                </template>

                <template v-else>
                  <div class="mt-2">
                    <div class="flex items-center justify-between mb-1.5">
                      <p class="text-xs text-gray-500 uppercase tracking-wider">Add to simulation</p>
                      <button
                        class="text-xs text-[#3C83F8] hover:text-blue-300 font-medium"
                        :disabled="!referential.backendAvailable"
                        @click="showCreateForm = true"
                      >+ New</button>
                    </div>
                    <USelectMenu
                      v-model="assetToAdd"
                      :items="availableForDropdown"
                      value-attribute="value"
                      searchable
                      search-placeholder="Search assets..."
                      placeholder="Select an asset..."
                      class="w-full"
                      :disabled="!referential.backendAvailable || availableForDropdown.length === 0"
                      @update:model-value="handleAddAsset"
                    >
                      <template #item="{ item }">
                        <div class="flex items-center justify-between w-full gap-2">
                          <span class="flex-1 truncate">{{ item.label }}</span>
                          <button
                            class="text-gray-700 hover:text-gray-500 flex-shrink-0 rounded"
                            @click.stop.prevent="deleteTarget = { id: item.value as string, name: (item as any).name ?? item.label, group: activeGroup }"
                          >
                            <UIcon name="i-heroicons-trash" class="w-3 h-3" />
                          </button>
                        </div>
                      </template>
                    </USelectMenu>
                  </div>

                  <div v-if="selectedAssetsList.length" class="border-t border-[#1E293B] pt-2 space-y-1.5">
                    <div
                      v-for="asset in selectedAssetsList"
                      :key="asset.id"
                      class="rounded-lg bg-[#020617] border overflow-hidden"
                      :class="expandedAssetId === asset.id ? 'border-[#3C83F8]/50' : 'border-[#1E293B]'"
                    >
                      <div class="p-2 cursor-pointer select-none" @click="toggleExpand(asset.id)">
                        <div class="flex items-start justify-between gap-1">
                          <div class="flex-1 min-w-0">
                            <div class="flex items-center gap-1.5 flex-wrap">
                              <UiAssetTypeIcon :type="asset.type" size="xs" />
                              <p class="text-xs font-semibold text-white truncate">{{ asset.name }}</p>
                              <span v-if="hasOverridesFor(asset.id)" class="text-xs px-1 py-0.5 bg-amber-900/40 text-amber-400 rounded leading-none">Edited</span>
                            </div>
                            <p class="text-xs text-gray-500 mt-0.5 truncate">{{ assetSummary(asset) }}</p>
                          </div>
                          <UIcon
                            :name="expandedAssetId === asset.id ? 'i-heroicons-chevron-up' : 'i-heroicons-chevron-down'"
                            class="w-3 h-3 text-gray-600 shrink-0 mt-0.5"
                          />
                          <button class="text-red-400 hover:text-red-300 shrink-0 mt-0.5" @click.stop="removeFromSelection(asset.id)">
                            <UIcon name="i-heroicons-x-mark" class="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                      <div v-if="expandedAssetId === asset.id" class="border-t border-[#1E293B] p-2 space-y-2 bg-[#0a111e]">
                        <p class="text-xs text-gray-500 uppercase tracking-wider mb-1">Parameters</p>
                        <template v-if="'load_mw' in asset">
                          <div>
                            <label class="text-xs text-gray-400 block mb-0.5">Load (MW)</label>
                            <UInput
                              :model-value="getOverrideValue(asset.id, 'load_mw', (asset as Demand).load_mw)"
                              type="number" size="xs"
                              @update:model-value="setOverrideValue(asset.id, 'load_mw', $event)"
                            />
                          </div>
                        </template>
                        <button v-if="hasOverridesFor(asset.id)" class="text-xs text-gray-500 hover:text-gray-300 mt-1" @click="clearOverridesFor(asset.id)">↺ Reset</button>
                      </div>
                    </div>
                  </div>
                  <p v-else class="text-xs text-gray-600 text-center py-2">No demand selected</p>
                </template>
              </div>
            </div>

            <!-- ── Section: Network ── -->
            <div class="border-b border-[#1E293B]">
              <button
                class="w-full flex items-center gap-2 px-3 py-2.5 text-sm font-medium hover:bg-[#1E293B]/60 transition-colors cursor-pointer"
                :class="activeGroup === 'Network' ? 'text-[#3C83F8]' : 'text-gray-300'"
                @click="setActiveGroup('Network')"
              >
                <UIcon name="i-heroicons-share" class="w-3.5 h-3.5 text-blue-400 shrink-0" />
                <span class="uppercase tracking-wider text-xs font-bold flex-1 text-left">Network</span>
                <span
                  v-if="store.selectedNetworkIds.length"
                  class="text-xs px-1.5 py-0.5 rounded bg-[#1E293B] text-gray-300 font-mono leading-none"
                >{{ store.selectedNetworkIds.length }}</span>
                <UIcon
                  :name="activeGroup === 'Network' ? 'i-heroicons-chevron-up' : 'i-heroicons-chevron-right'"
                  class="w-3 h-3 text-gray-500 shrink-0"
                />
              </button>

              <div v-if="activeGroup === 'Network'" class="px-3 pb-3 space-y-3">
                <template v-if="showCreateForm">
                  <div class="flex items-center justify-between mt-2 mb-1">
                    <p class="text-xs font-semibold text-[#3C83F8] uppercase tracking-wider">New Network asset</p>
                    <button class="text-xs text-gray-500 hover:text-gray-300" @click="showCreateForm = false">✕ Cancel</button>
                  </div>
                  <div class="space-y-2">
                    <div>
                      <label class="text-xs text-gray-400 block mb-0.5">Type</label>
                      <USelect
                        v-model="createNetworkForm.type"
                        :items="[
                          { label: 'Transformer', value: 'transformer' },
                          { label: 'Cable', value: 'cable' },
                        ]"
                        size="sm" class="w-full"
                      />
                    </div>
                    <div>
                      <label class="text-xs text-gray-400 block mb-0.5">Name</label>
                      <UInput v-model="createNetworkForm.name" size="sm" placeholder="e.g. HV Transformer 01" />
                    </div>
                    <div>
                      <label class="text-xs text-gray-400 block mb-0.5">Voltage (kV)</label>
                      <UInput v-model="createNetworkForm.voltage_kv" type="number" size="sm" />
                    </div>
                    <div>
                      <label class="text-xs text-gray-400 block mb-0.5">Capacity (MVA)</label>
                      <UInput v-model="createNetworkForm.capacity_mva" type="number" size="sm" />
                    </div>
                  </div>
                  <UButton
                    block icon="i-heroicons-plus" label="Create and add"
                    color="primary" size="sm"
                    :loading="isSaving" :disabled="isSaving || !referential.backendAvailable"
                    @click="handleCreate"
                  />
                </template>

                <template v-else>
                  <div class="mt-2">
                    <div class="flex items-center justify-between mb-1.5">
                      <p class="text-xs text-gray-500 uppercase tracking-wider">Add to simulation</p>
                      <button
                        class="text-xs text-[#3C83F8] hover:text-blue-300 font-medium"
                        :disabled="!referential.backendAvailable"
                        @click="showCreateForm = true"
                      >+ New</button>
                    </div>
                    <USelectMenu
                      v-model="assetToAdd"
                      :items="availableForDropdown"
                      value-attribute="value"
                      searchable
                      search-placeholder="Search assets..."
                      placeholder="Select an asset..."
                      class="w-full"
                      :disabled="!referential.backendAvailable || availableForDropdown.length === 0"
                      @update:model-value="handleAddAsset"
                    >
                      <template #item="{ item }">
                        <div class="flex items-center justify-between w-full gap-2">
                          <span class="flex-1 truncate">{{ item.label }}</span>
                          <button
                            class="text-gray-700 hover:text-gray-500 flex-shrink-0 rounded"
                            @click.stop.prevent="deleteTarget = { id: item.value as string, name: (item as any).name ?? item.label, group: activeGroup }"
                          >
                            <UIcon name="i-heroicons-trash" class="w-3 h-3" />
                          </button>
                        </div>
                      </template>
                    </USelectMenu>
                  </div>

                  <div v-if="selectedAssetsList.length" class="border-t border-[#1E293B] pt-2 space-y-1.5">
                    <div
                      v-for="asset in selectedAssetsList"
                      :key="asset.id"
                      class="rounded-lg bg-[#020617] border overflow-hidden"
                      :class="expandedAssetId === asset.id ? 'border-[#3C83F8]/50' : 'border-[#1E293B]'"
                    >
                      <div class="p-2 cursor-pointer select-none" @click="toggleExpand(asset.id)">
                        <div class="flex items-start justify-between gap-1">
                          <div class="flex-1 min-w-0">
                            <div class="flex items-center gap-1.5 flex-wrap">
                              <UiAssetTypeIcon :type="asset.type" size="xs" />
                              <p class="text-xs font-semibold text-white truncate">{{ asset.name }}</p>
                              <span v-if="hasOverridesFor(asset.id)" class="text-xs px-1 py-0.5 bg-amber-900/40 text-amber-400 rounded leading-none">Edited</span>
                            </div>
                            <p class="text-xs text-gray-500 mt-0.5 truncate">{{ assetSummary(asset) }}</p>
                          </div>
                          <UIcon
                            :name="expandedAssetId === asset.id ? 'i-heroicons-chevron-up' : 'i-heroicons-chevron-down'"
                            class="w-3 h-3 text-gray-600 shrink-0 mt-0.5"
                          />
                          <button class="text-red-400 hover:text-red-300 shrink-0 mt-0.5" @click.stop="removeFromSelection(asset.id)">
                            <UIcon name="i-heroicons-x-mark" class="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                      <div v-if="expandedAssetId === asset.id" class="border-t border-[#1E293B] p-2 space-y-2 bg-[#0a111e]">
                        <p class="text-xs text-gray-500 uppercase tracking-wider mb-1">Parameters</p>
                        <template v-if="'capacity_mva' in asset">
                          <div>
                            <label class="text-xs text-gray-400 block mb-0.5">Capacity (MVA)</label>
                            <UInput
                              :model-value="getOverrideValue(asset.id, 'capacity_mva', (asset as NetworkComponent).capacity_mva)"
                              type="number" size="xs"
                              @update:model-value="setOverrideValue(asset.id, 'capacity_mva', $event)"
                            />
                          </div>
                        </template>
                        <button v-if="hasOverridesFor(asset.id)" class="text-xs text-gray-500 hover:text-gray-300 mt-1" @click="clearOverridesFor(asset.id)">↺ Reset</button>
                      </div>
                    </div>
                  </div>
                  <p v-else class="text-xs text-gray-600 text-center py-2">No network component selected</p>
                </template>
              </div>
            </div>

            <!-- Loading spinner -->
            <div v-if="referential.referentialLoading" class="flex justify-center py-4">
              <div class="animate-spin h-5 w-5 border-t-2 border-[#3C83F8] rounded-full" />
            </div>
          </div>

          <!-- ── Sidebar footer ── -->
          <div class="border-t border-[#1E293B] p-3 flex flex-col gap-2 shrink-0">
            <div class="text-xs text-gray-600 text-center font-mono">
              {{ store.selectedSupplyIds.length }}S · {{ store.selectedDemandIds.length }}D · {{ store.selectedNetworkIds.length }}N selected
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
        </aside>
      </Transition>

      <!-- ── Main content ──────────────────────────────────────────────────────── -->
      <main class="flex-1 overflow-y-auto pb-10">
        <NuxtPage />
      </main>
    </div>

    <!-- ── Bottom KPI bar ────────────────────────────────────────────────────── -->
    <footer class="bg-[#0F172A] border-t border-[#1E293B] shrink-0 relative overflow-hidden">
      <!-- Running progress line -->
      <div
        v-if="store.isLiveRunning"
        class="absolute top-0 left-0 h-0.5 bg-amber-400/60 animate-pulse w-full"
      />

      <div class="h-10 flex items-center px-4 gap-0 text-xs">
        <!-- Status -->
        <div class="flex items-center gap-2 px-3 border-r border-[#1E293B]">
          <span class="text-gray-500 uppercase tracking-wider">Status</span>
          <span class="flex items-center gap-1">
            <span
              class="inline-block h-1.5 w-1.5 rounded-full"
              :class="kpiStatus === 'optimal' ? 'bg-emerald-400'
                : kpiStatus === 'error' ? 'bg-red-500'
                : kpiStatus === 'running' ? 'bg-amber-400 animate-pulse'
                : 'bg-gray-600'"
            />
            <span
              class="font-semibold transition-colors duration-300"
              :class="kpiStatus === 'optimal' ? 'text-emerald-400'
                : kpiStatus === 'error' ? 'text-red-400'
                : kpiStatus === 'running' ? 'text-amber-400'
                : 'text-gray-500'"
            >
              {{ kpiStatus === 'optimal' ? 'Optimal' : kpiStatus === 'error' ? 'Infeasible' : kpiStatus === 'running' ? 'Running…' : '—' }}
            </span>
          </span>
        </div>

        <!-- Total Supply -->
        <div class="flex items-center gap-2 px-3 border-r border-[#1E293B]">
          <span class="text-gray-500 uppercase tracking-wider">Supply</span>
          <span class="font-mono text-white transition-all duration-300">{{ kpiSupply }}</span>
          <span class="text-gray-600">MWh</span>
        </div>

        <!-- Total Demand -->
        <div class="flex items-center gap-2 px-3 border-r border-[#1E293B]">
          <span class="text-gray-500 uppercase tracking-wider">Demand</span>
          <span class="font-mono text-white transition-all duration-300">{{ kpiDemand }}</span>
          <span class="text-gray-600">MWh</span>
        </div>

        <!-- Balance -->
        <div class="flex items-center gap-2 px-3 border-r border-[#1E293B]">
          <span class="text-gray-500 uppercase tracking-wider">Balance</span>
          <span class="font-mono transition-all duration-300" :class="kpiBalanceColor">{{ kpiBalance }}</span>
          <span class="text-gray-600">MWh</span>
        </div>

        <!-- Asset counts -->
        <div class="flex items-center gap-2 px-3">
          <span class="text-gray-500 uppercase tracking-wider">Assets</span>
          <span class="font-mono text-gray-300">
            {{ store.selectedSupplyIds.length }}S · {{ store.selectedDemandIds.length }}D · {{ store.selectedNetworkIds.length }}N
          </span>
        </div>

        <div class="flex-1" />

        <!-- Running indicator -->
        <div v-if="store.isLiveRunning" class="flex items-center gap-1.5 text-amber-400 pr-2">
          <div class="animate-spin h-3 w-3 border-t border-amber-400 rounded-full" />
          <span>Optimizing…</span>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import {
  fetchScenarioExport,
  fetchSimulationSolvers,
  type Demand,
  type NetworkComponent,
  type ScenarioExport,
  type SimulationSolverInfo,
  type Supply,
} from '~/composables/api'
import { useSimulationStore } from '~/stores/simulation'
import { useReferentialStore } from '~/stores/referential'
import { useHistoryStore } from '~/stores/history'
import { useLiveRunner } from '~/composables/useLiveRunner'

const store = useSimulationStore()
const referential = useReferentialStore()
const history = useHistoryStore()
const toast = useToast()

// ─── Date mode toggle (Hours vs Date Range) ────────────────────────────────────

const dateMode = ref<'hours' | 'dates'>('hours')


const todayMonthDay = new Date().toISOString().slice(5, 10) // "MM-DD"
const DEFAULT_START = `2025-${todayMonthDay}`
const DEFAULT_END = `2025-${todayMonthDay}`

function setDateMode(mode: 'hours' | 'dates') {
  dateMode.value = mode
  if (mode === 'dates') {
    if (!store.startDate) store.startDate = DEFAULT_START
    if (!store.endDate) store.endDate = DEFAULT_END
  } else {
    store.startDate = ''
    store.endDate = ''
  }
}

// ─── Live simulation ───────────────────────────────────────────────────────────

const { runPreview, saveSimulation } = useLiveRunner()

// Auto-run whenever any parameter changes (debounced inside runPreview)
watch(
  () => JSON.stringify(store.buildPayload()),
  () => {
    if (!referential.backendAvailable || !store.hasMinimumAssets) return
    if (!store.isLiveMode) return
    runPreview(store.buildPayload())
  },
)

// Warn once when solar/wind assets are selected but no dates are set
const _noDateWarnShown = ref(false)
watch(
  () => ({ ids: store.selectedSupplyIds, start: store.startDate }),
  ({ ids, start }) => {
    if (start) { _noDateWarnShown.value = false; return }
    if (_noDateWarnShown.value) return
    const hasWeatherAsset = store.selectedSupplies.some(
      (s) => s.type === 'solar_panel' || s.type === 'wind_turbine',
    )
    if (!hasWeatherAsset) return
    _noDateWarnShown.value = true
    toast.add({
      title: 'No date range selected',
      description: 'Solar and wind assets will run at rated capacity (p_nom) without a real weather profile. Select a date range for realistic results.',
      color: 'warning',
      duration: 8000,
    })
  },
  { deep: false },
)

// ─── Header: rename selected scenario ─────────────────────────────────────────

const handleHeaderRename = async () => {
  const id = history.selectedSimulationId
  const name = store.scenarioName.trim()
  if (!id || !name) return
  try {
    await history.renameEntry(id, name)
    toast.add({ title: 'Scenario renamed', color: 'success' })
  } catch {
    toast.add({ title: 'Rename failed', color: 'error' })
  }
}

// ─── Save handler ──────────────────────────────────────────────────────────────

const showSaveChoiceModal = ref(false)

function _buildSavePayload() {
  return { ...store.buildPayload(), name: store.scenarioName || undefined }
}

async function _doSave(payload: ReturnType<typeof _buildSavePayload>) {
  try {
    const result = await saveSimulation(payload)
    // Point to the newly saved simulation so the selector stays consistent
    history.currentResult = result
    history.selectedSimulationId = result.id
    store.selectedHistoryId = result.id
    if (result.status === 'error') {
      const errorType = result.result_json?.error_type
      const solver = result.result_json?.solver ?? store.solver
      const backendError = result.result_json?.error
      const description = errorType === 'solver_error'
        ? `Solver '${solver}' unavailable or misconfigured.${backendError ? ` ${backendError}` : ''}`
        : `${backendError ?? 'PyPSA did not find an optimal solution.'} (solver: ${solver})`
      toast.add({
        title: errorType === 'solver_error' ? 'Solver execution error' : 'Simulation failed',
        description,
        color: 'error',
      })
    } else {
      toast.add({ title: 'Simulation saved', description: `Status: ${result.status}`, color: 'success' })
      for (const msg of result.result_json?.warnings ?? []) {
        toast.add({
          title: 'Weather data warning',
          description: msg,
          color: 'warning',
          duration: 8000,
        })
      }
    }
  } catch {
    toast.add({ title: 'Save error', description: store.error ?? 'Failed to save simulation', color: 'error' })
  }
}

const handleSave = () => {
  if (!referential.backendAvailable) {
    toast.add({ title: 'Backend unavailable', description: 'Start the API server first', color: 'warning' })
    return
  }
  if (!store.hasMinimumAssets) {
    toast.add({ title: 'Incomplete selection', description: 'Select at least one supply and one demand', color: 'warning' })
    return
  }
  // If a reference sim exists, ask Replace or New
  if (store.referenceSimId !== null) {
    showSaveChoiceModal.value = true
    return
  }
  _doSave(_buildSavePayload())
}

const handleSaveReplace = async () => {
  showSaveChoiceModal.value = false
  // Delete the old simulation first, then save with same payload
  try {
    await history.deleteEntry(store.referenceSimId!)
  } catch { /* already deleted or not found — proceed anyway */ }
  await _doSave(_buildSavePayload())
}

function _generateCopyName(baseName: string): string {
  const existingNames = new Set(history.simulationHistory.map(s => s.name))
  const candidate = `${baseName} (copy)`
  if (!existingNames.has(candidate)) return candidate
  let i = 2
  while (existingNames.has(`${baseName} (#${i})`)) i++
  return `${baseName} (#${i})`
}

const handleSaveNew = async () => {
  showSaveChoiceModal.value = false
  const payload = _buildSavePayload()
  if (payload.name) {
    payload.name = _generateCopyName(payload.name)
    store.scenarioName = payload.name
  }
  await _doSave(payload)
}

// ─── Sidebar state ─────────────────────────────────────────────────────────────

const sidebarOpen = ref(true)
const activeGroup = ref('Supply')
const assetToAdd = ref('')
const showCreateForm = ref(false)
const isSaving = ref(false)
const expandedAssetId = ref<string | null>(null)

function setActiveGroup(group: string) {
  if (activeGroup.value === group) return
  activeGroup.value = group
}

// ─── Solver availability ───────────────────────────────────────────────────────

const fileInput = ref<HTMLInputElement | null>(null)
const showSolverHelpModal = ref(false)
const solverAvailabilityLoading = ref(false)
const solverAvailabilityByName = ref<Record<string, SimulationSolverInfo>>({})

const solverOptions = [
  { label: 'HiGHS', value: 'highs', description: 'Minimizes total operating cost — fast LP, open-source (default)', speed: 'Fast', license: 'Open-source', bestFor: 'Default choice for most LP economic dispatch simulations' },
  { label: 'GLPK', value: 'glpk', description: 'Minimizes total cost — reliable LP/MIP but slower, open-source', speed: 'Slow', license: 'Open-source', bestFor: 'Simple runs and compatibility checks' },
  { label: 'CBC', value: 'cbc', description: 'Optimizes ON/OFF unit commitment decisions — MIP open-source (COIN-OR)', speed: 'Medium', license: 'Open-source', bestFor: 'Mixed-integer problems with binary commitments' },
  { label: 'SCIP', value: 'scip', description: 'Solves complex MIP problems with constraints — academic solver', speed: 'Medium', license: 'Academic', bestFor: 'Complex MIP formulations in research contexts' },
  { label: 'Gurobi', value: 'gurobi', description: 'Minimizes cost or emissions ultra-fast — LP/MIP commercial', speed: 'Very fast', license: 'Commercial', bestFor: 'Large-scale industrial optimization with strict runtime targets' },
  { label: 'CPLEX', value: 'cplex', description: 'Industrial-grade LP/MIP optimization — IBM, commercial', speed: 'Very fast', license: 'Commercial', bestFor: 'Enterprise-grade robust optimization workloads' },
  { label: 'Xpress', value: 'xpress', description: 'Large-scale LP/MIP optimization — FICO, commercial', speed: 'Very fast', license: 'Commercial', bestFor: 'High-performance LP/MIP on large utility-scale systems' },
] as const

const solverSelectItems = computed(() =>
  solverOptions.map(({ label, value }) => {
    const info = solverAvailabilityByName.value[value]
    const isUnavailable = info ? !info.available : false
    return { label: isUnavailable ? `${label} (unavailable)` : label, value, disabled: isUnavailable }
  }),
)

const selectedSolverTitle = computed(() => {
  const selected = solverOptions.find(o => o.value === store.solver)
  if (!selected) return 'Solver'
  const info = solverAvailabilityByName.value[selected.value]
  if (info && !info.available) return `${selected.label} - ${selected.description}. Unavailable: ${info.reason ?? 'not installed'}`
  return `${selected.label} - ${selected.description}`
})

const selectedSolverLabel = computed(() => {
  const selected = solverOptions.find(o => o.value === store.solver)
  if (!selected) return 'Unknown'
  const info = solverAvailabilityByName.value[selected.value]
  return info && !info.available ? `${selected.label} (unavailable)` : selected.label
})

const refreshSolverAvailability = async () => {
  solverAvailabilityLoading.value = true
  try {
    const solvers = await fetchSimulationSolvers()
    solverAvailabilityByName.value = Object.fromEntries(solvers.map(s => [s.name, s]))
  } catch {
    solverAvailabilityByName.value = {}
  } finally {
    solverAvailabilityLoading.value = false
  }
}

const isSolverUnavailable = (solverName: string): boolean => {
  const info = solverAvailabilityByName.value[solverName]
  return info ? !info.available : false
}

const solverUnavailableReason = (solverName: string): string => {
  const info = solverAvailabilityByName.value[solverName]
  if (!info || info.available) return ''
  return info.reason ?? 'Solver not available on backend.'
}

// ─── Export / Import ──────────────────────────────────────────────────────────

const handleExport = async () => {
  const id = history.selectedSimulationId ?? history.currentResult?.id
  if (!id) return
  try {
    const scenario = await fetchScenarioExport(id)
    const name = history.currentResult?.name ?? id
    const filename = `scenario-${name}-${new Date().toISOString().slice(0, 10)}.json`
    const blob = new Blob([JSON.stringify(scenario, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    toast.add({ title: 'Export error', color: 'error' })
  }
}

const handleImport = (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const scenario = JSON.parse(e.target?.result as string) as ScenarioExport
      store.loadFromScenario(scenario, file.name.replace('.json', ''))
      // Restore date mode based on loaded scenario
      dateMode.value = (scenario.start_date && scenario.end_date) ? 'dates' : 'hours'
      toast.add({ title: 'Scenario loaded', color: 'success' })
    } catch {
      toast.add({ title: 'Invalid file', color: 'error' })
    } finally {
      if (fileInput.value) fileInput.value.value = ''
    }
  }
  reader.readAsText(file)
}

// ─── Delete asset ─────────────────────────────────────────────────────────────

const deleteTarget = ref<{ id: string; name: string; group: string } | null>(null)
const isDeleting = ref(false)

const showDeleteModal = computed({
  get: () => deleteTarget.value !== null,
  set: (val: boolean) => { if (!val) deleteTarget.value = null },
})

const handleDeleteAsset = async () => {
  if (!deleteTarget.value) return
  isDeleting.value = true
  try {
    const { id, group } = deleteTarget.value
    if (group === 'Supply') await store.removeSupply(id)
    else if (group === 'Demand') await store.removeDemand(id)
    else await store.removeNetworkComponent(id)
    toast.add({ title: 'Asset deleted', color: 'success' })
    deleteTarget.value = null
  } catch (e: unknown) {
    toast.add({ title: 'Deletion error', description: e instanceof Error ? e.message : 'Unknown error', color: 'error' })
  } finally {
    isDeleting.value = false
  }
}

// ─── Display helpers ───────────────────────────────────────────────────────────

function assetSummary(asset: Supply | Demand | NetworkComponent): string {
  if ('capacity_mw' in asset) return `${asset.capacity_mw} MW · eff ${asset.efficiency}`
  if ('load_mw' in asset) return `${asset.load_mw} MW`
  if ('voltage_kv' in asset) return `${asset.voltage_kv} kV · ${asset.capacity_mva} MVA`
  return ''
}

// ─── Computed selection ────────────────────────────────────────────────────────

const availableForDropdown = computed(() => {
  if (activeGroup.value === 'Supply') {
    return referential.availableSupplies
      .filter((s: Supply) => !store.selectedSupplyIds.includes(s.id))
      .map((s: Supply) => ({ label: s.name, value: s.id, name: s.name }))
  }
  if (activeGroup.value === 'Demand') {
    return referential.availableDemands
      .filter((d: Demand) => !store.selectedDemandIds.includes(d.id))
      .map((d: Demand) => ({ label: d.name, value: d.id, name: d.name }))
  }
  if (activeGroup.value === 'Network') {
    return referential.availableNetwork
      .filter((n: NetworkComponent) => !store.selectedNetworkIds.includes(n.id))
      .map((n: NetworkComponent) => ({ label: n.name, value: n.id, name: n.name }))
  }
  return []
})

const selectedAssetsList = computed<Array<Supply | Demand | NetworkComponent>>(() => {
  if (activeGroup.value === 'Supply') return store.selectedSupplies
  if (activeGroup.value === 'Demand') return store.selectedDemands
  if (activeGroup.value === 'Network') return store.selectedNetwork
  return []
})

// ─── Selection actions ─────────────────────────────────────────────────────────

const handleAddAsset = (val: string | { value: string } | null) => {
  const id = val && typeof val === 'object' ? val.value : val
  if (!id) return
  if (!store.isLiveMode) store.selectedHistoryId = null  // switch to live mode on edit
  if (activeGroup.value === 'Supply') store.addSupplyToSelection(id)
  else if (activeGroup.value === 'Demand') store.addDemandToSelection(id)
  else store.addNetworkToSelection(id)
  nextTick(() => { assetToAdd.value = '' })
}

const removeFromSelection = (id: string) => {
  if (expandedAssetId.value === id) expandedAssetId.value = null
  if (!store.isLiveMode) store.selectedHistoryId = null  // switch to live mode on edit
  if (activeGroup.value === 'Supply') store.removeSupplyFromSelection(id)
  else if (activeGroup.value === 'Demand') store.removeDemandFromSelection(id)
  else store.removeNetworkFromSelection(id)
}

watch(activeGroup, () => {
  assetToAdd.value = ''
  showCreateForm.value = false
  expandedAssetId.value = null
})

watch(
  solverSelectItems,
  (items) => {
    const current = items.find(item => item.value === store.solver)
    if (current && !current.disabled) return
    const fallback = items.find(item => !item.disabled)
    if (!fallback || store.solver === fallback.value) return
    const previousSolver = store.solver
    store.solver = fallback.value
    toast.add({ title: 'Solver switched', description: `Solver '${previousSolver}' is unavailable. Switched to '${fallback.value}'.`, color: 'warning' })
  },
  { immediate: true },
)

watch(
  () => referential.backendAvailable,
  (available) => { if (available) void refreshSolverAvailability() },
  { immediate: true },
)

// ─── Override helpers ──────────────────────────────────────────────────────────

function currentGroupType(): 'supply' | 'demand' | 'network' {
  if (activeGroup.value === 'Supply') return 'supply'
  if (activeGroup.value === 'Demand') return 'demand'
  return 'network'
}

function toggleExpand(id: string) {
  expandedAssetId.value = expandedAssetId.value === id ? null : id
}

function hasOverridesFor(id: string): boolean {
  return store.hasOverrides(currentGroupType(), id)
}

function getOverrideValue(id: string, field: string, defaultVal: number): number {
  const assetOverrides = store.getOverrides(currentGroupType(), id)
  return field in assetOverrides ? assetOverrides[field] : defaultVal
}

function setOverrideValue(id: string, field: string, rawValue: string | number) {
  const value = typeof rawValue === 'string' ? parseFloat(rawValue) : rawValue
  if (!isNaN(value)) {
    if (!store.isLiveMode) store.selectedHistoryId = null  // switch to live mode on edit
    store.setOverride(currentGroupType(), id, field, value)
  }
}

function clearOverridesFor(id: string) {
  store.clearOverrides(currentGroupType(), id)
}

// ─── Create forms ──────────────────────────────────────────────────────────────

const createSupplyForm = reactive({
  type: 'wind_turbine' as 'wind_turbine' | 'solar_panel' | 'nuclear_plant',
  name: '',
  capacity_mw: 500,
  efficiency: 0.42,
  status: 'active' as const,
  unit: 'MW',
  description: '',
})

const createDemandForm = reactive({
  type: 'house' as 'house' | 'electric_vehicle',
  name: '',
  load_mw: 120,
  status: 'active' as const,
  unit: 'MW',
  description: '',
})

const createNetworkForm = reactive({
  type: 'transformer' as 'transformer' | 'cable',
  name: '',
  voltage_kv: 400,
  capacity_mva: 500,
  status: 'active' as const,
  unit: 'MVA',
  description: '',
})

const handleCreate = async () => {
  isSaving.value = true
  try {
    if (activeGroup.value === 'Supply') {
      const created = await referential.addSupply({ ...createSupplyForm })
      store.addSupplyToSelection(created.id)
      createSupplyForm.name = ''
    } else if (activeGroup.value === 'Demand') {
      const created = await referential.addDemand({ ...createDemandForm })
      store.addDemandToSelection(created.id)
      createDemandForm.name = ''
    } else {
      const created = await referential.addNetworkComponent({
        ...createNetworkForm,
        losses_kw: null,
        voltage_hv_kv: null,
        voltage_lv_kv: null,
        length_km: null,
        resistance_ohm_per_km: null,
        reactance_ohm_per_km: null,
      })
      store.addNetworkToSelection(created.id)
      createNetworkForm.name = ''
    }
    toast.add({ title: 'Asset created and added to simulation', color: 'success' })
    showCreateForm.value = false
  } catch (e: unknown) {
    toast.add({ title: 'Error', description: e instanceof Error ? e.message : 'Unknown error', color: 'error' })
  } finally {
    isSaving.value = false
  }
}

// ─── Bottom KPI bar data ───────────────────────────────────────────────────────

const kpiResult = computed(() => store.displayedResult)

const kpiStatus = computed(() => {
  if (store.isLiveRunning || store.isRunning) return 'running'
  return kpiResult.value?.status ?? null
})

const kpiSupply = computed(() => {
  const v = kpiResult.value?.total_supply_mwh
  return v != null ? v.toFixed(2) : '—'
})

const kpiDemand = computed(() => {
  const v = kpiResult.value?.total_demand_mwh
  return v != null ? v.toFixed(2) : '—'
})

const kpiBalance = computed(() => {
  const v = kpiResult.value?.balance_mwh
  return v != null ? v.toFixed(2) : '—'
})

const kpiBalanceColor = computed(() => {
  const v = kpiResult.value?.balance_mwh
  if (v == null || kpiResult.value?.status === 'error') return 'text-gray-500'
  if (Math.abs(v) < 0.001) return 'text-emerald-400'
  return v > 0 ? 'text-blue-400' : 'text-red-400'
})
</script>

<style scoped>
.sidebar-enter-active,
.sidebar-leave-active {
  transition: width 0.3s ease, opacity 0.2s ease;
  width: 240px;
}
.sidebar-enter-from,
.sidebar-leave-to {
  width: 0;
  opacity: 0;
}
</style>
