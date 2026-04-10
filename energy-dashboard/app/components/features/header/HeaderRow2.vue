<template>
  <div class="flex items-center gap-3 px-4 h-10 border-t border-[#1E293B] bg-[#020617]/40">
    <!-- Duration mode toggle -->
    <div class="flex items-center gap-0 rounded border border-[#334155] overflow-hidden shrink-0">
      <button
        class="px-2.5 h-6 text-xs transition-colors"
        :class="dateMode === 'hours' ? 'bg-[#1E293B] text-white' : 'bg-transparent text-gray-500 hover:text-gray-300'"
        @click="setDateMode('hours')"
      >
        Hours
      </button>
      <button
        class="px-2.5 h-6 text-xs transition-colors border-l border-[#334155]"
        :class="dateMode === 'dates' ? 'bg-[#1E293B] text-white' : 'bg-transparent text-gray-500 hover:text-gray-300'"
        @click="setDateMode('dates')"
      >
        Date range
      </button>
    </div>

    <!-- Hours selector -->
    <div
      v-if="dateMode === 'hours'"
      class="flex items-center gap-1.5"
    >
      <USelect
        v-model="store.snapshotHours"
        :items="[
          { label: '1 h', value: 1 },
          { label: '24 h', value: 24 },
          { label: '168 h', value: 168 },
          { label: '8760 h', value: 8760 }
        ]"
        class="w-24"
        size="xs"
      />
      <UTooltip text="Number of hourly snapshots to simulate. Each snapshot is one AC power flow calculation. Total energy (MWh) = installed capacity (MW) × number of hours × capacity factor. More hours = more realistic averaging but longer computation.">
        <UIcon name="i-heroicons-information-circle" class="w-3.5 h-3.5 text-gray-600 cursor-help shrink-0" />
      </UTooltip>
    </div>

    <!-- Date range picker -->
    <div
      v-else
      class="flex items-center gap-0 rounded border border-[#334155] overflow-hidden"
    >
      <input
        v-model="store.startDate"
        type="date"
        min="2025-01-01"
        max="2025-12-31"
        class="h-6 px-1.5 text-xs bg-[#0F172A] text-white focus:outline-none focus:bg-[#0F172A]/80 w-32 border-0"
      >
      <span class="text-xs text-gray-600 px-1 shrink-0 border-x border-[#334155]">→</span>
      <input
        v-model="store.endDate"
        type="date"
        min="2025-01-01"
        max="2025-12-31"
        class="h-6 px-1.5 text-xs bg-[#0F172A] text-white focus:outline-none focus:bg-[#0F172A]/80 w-32 border-0"
      >
      <span
        v-if="store.startDate && store.endDate"
        class="text-xs text-emerald-400 font-mono px-1.5 border-l border-[#334155] shrink-0"
      >{{ store.snapshotHours }}h</span>
    </div>

    <!-- Solver selector -->
    <div
      class="flex items-center gap-1.5"
      :title="selectedSolverTitle"
    >
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
        @click="$emit('open-solver-help')"
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
        @click="$emit('header-rename')"
      />
    </div>

    <!-- Import -->
    <input
      ref="fileInputRef"
      type="file"
      accept=".json"
      class="hidden"
      @change="handleImport"
    >
    <UButton
      icon="i-heroicons-arrow-up-tray"
      label="Import"
      size="xs"
      color="neutral"
      variant="outline"
      @click="fileInputRef?.click()"
    />

    <div class="flex-1" />

    <!-- Live indicator -->
    <div class="flex items-center gap-1.5 select-none">
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
  </div>
</template>

<script setup lang="ts">
import { useSimulationStore } from '~/stores/simulation'
import { useReferentialStore } from '~/stores/referential'
import { useHistoryStore } from '~/stores/history'

defineEmits<{
  'open-solver-help': []
  'header-rename': []
}>()

const store = useSimulationStore()
const referential = useReferentialStore()
const history = useHistoryStore()

const { dateMode, setDateMode, handleImport, fileInputRef } = useScenarioIO()
const { solverSelectItems, solverAvailabilityLoading, selectedSolverTitle } = useSolverAvailability()

</script>
