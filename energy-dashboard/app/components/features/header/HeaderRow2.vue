<template>
  <div class="flex items-center gap-3 px-4 h-10 border-t border-gray-200 dark:border-slate-800 bg-gray-50/40 dark:bg-slate-950/40">
    <!-- Duration mode toggle -->
    <div class="flex items-center gap-0 rounded border border-gray-300 dark:border-slate-700 overflow-hidden shrink-0">
      <button
        class="px-2.5 h-6 text-xs transition-colors"
        :class="dateMode === 'hours' ? 'bg-gray-200 text-gray-900 dark:bg-slate-800 dark:text-white' : 'bg-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'"
        @click="setDateMode('hours')"
      >
        {{ $t('header.hours') }}
      </button>
      <button
        class="px-2.5 h-6 text-xs transition-colors border-l border-gray-300 dark:border-slate-700"
        :class="dateMode === 'dates' ? 'bg-gray-200 text-gray-900 dark:bg-slate-800 dark:text-white' : 'bg-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'"
        @click="setDateMode('dates')"
      >
        {{ $t('header.dateRange') }}
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
      <UTooltip text="Number of hourly snapshots. The LOPF optimises all hours simultaneously — batteries can shift energy across the whole period. Total energy (MWh) = installed capacity (MW) × hours × capacity factor. More hours = more realistic averaging.">
        <UIcon
          name="i-heroicons-information-circle"
          class="w-3.5 h-3.5 text-gray-600 cursor-help shrink-0"
        />
      </UTooltip>
    </div>

    <!-- Date range picker -->
    <div
      v-else
      class="flex items-center gap-0 rounded border border-gray-300 dark:border-slate-700 overflow-hidden"
    >
      <input
        v-model="store.startDate"
        type="date"
        min="2025-01-01"
        max="2025-12-31"
        class="h-6 px-1.5 text-xs bg-white text-gray-900 dark:bg-slate-900 dark:text-white focus:outline-none focus:bg-gray-50 dark:focus:bg-slate-900/80 w-32 border-0"
      >
      <span class="text-xs text-gray-600 px-1 shrink-0 border-x border-gray-300 dark:border-slate-700">→</span>
      <input
        v-model="store.endDate"
        type="date"
        min="2025-01-01"
        max="2025-12-31"
        class="h-6 px-1.5 text-xs bg-white text-gray-900 dark:bg-slate-900 dark:text-white focus:outline-none focus:bg-gray-50 dark:focus:bg-slate-900/80 w-32 border-0"
      >
      <span
        v-if="store.startDate && store.endDate"
        class="text-xs text-emerald-400 font-mono px-1.5 border-l border-gray-300 dark:border-slate-700 shrink-0"
      >{{ store.snapshotHours }}h</span>
    </div>

    <!-- Solver selector -->
    <div
      class="flex items-center gap-1.5"
      :title="selectedSolverTitle"
    >
      <label class="text-xs text-gray-500">{{ $t('header.solver') }}</label>
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
        :title="$t('header.openSolverHelp')"
        @click="$emit('open-solver-help')"
      />
    </div>

    <!-- Optimization Objective selector -->
    <div class="flex items-center gap-1.5">
      <label class="text-xs text-gray-500">{{ $t('header.objective') }}</label>
      <USelect
        v-model="store.optimizationObjective"
        :items="objectiveSelectItems"
        class="w-44"
        size="xs"
      />
    </div>

    <!-- Scenario name + rename -->
    <div class="flex items-center gap-1">
      <UInput
        v-model="store.scenarioName"
        :placeholder="$t('header.scenarioNamePlaceholder')"
        size="xs"
        class="w-44"
      />
      <UButton
        icon="i-heroicons-pencil-square"
        size="xs"
        color="neutral"
        variant="ghost"
        :title="$t('header.renameScenario')"
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
      :label="$t('header.import')"
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
        {{ store.isLiveRunning ? $t('header.running') : store.hasMinimumAssets && referential.backendAvailable ? $t('header.live') : $t('header.idle') }}
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
const { t } = useI18n()

const { dateMode, setDateMode, handleImport, fileInputRef } = useScenarioIO()
const { solverSelectItems, solverAvailabilityLoading, selectedSolverTitle } = useSolverAvailability()

const objectiveSelectItems = computed(() => [
  { label: t('header.minimizeCost'), value: 'min_cost' },
  { label: t('header.minimizeEmissions'), value: 'min_emissions' },
  { label: t('header.maximizeRenewable'), value: 'max_renewable' }
])
</script>
