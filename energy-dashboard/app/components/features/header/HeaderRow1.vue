<template>
  <div class="flex items-center gap-2 px-4 h-14">
    <UButton
      variant="ghost"
      icon="i-heroicons-bars-3"
      color="neutral"
      @click="$emit('toggle-sidebar')"
    />

    <img
      src="/logo.png"
      alt="EnergyDash"
      class="h-8 w-auto"
    >

    <span class="font-semibold text-base text-gray-900 dark:text-white hidden sm:block">
      Energy Network Simulator 2026
    </span>

    <!-- Backend status badge -->
    <span
      class="text-xs px-2 py-1 rounded-full ml-2"
      :class="referential.backendAvailable === true
        ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-400'
        : referential.backendAvailable === false
          ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400'
          : 'bg-gray-200 text-gray-500 dark:bg-gray-800 dark:text-gray-500'"
    >
      {{ referential.backendAvailable === true ? '● Connected' : referential.backendAvailable === false ? '● Offline' : '● …' }}
    </span>

    <div class="flex-1" />

    <!-- Weather station indicator -->
    <div
      class="hidden sm:flex items-center gap-1 text-xs text-gray-500 border border-gray-200 dark:border-slate-800 rounded px-2 h-6 shrink-0"
      title="Weather data source: KNMI station 06280 — Groningen Eelde. Covers Jan 2025 → Dec 2025."
    >
      <UIcon
        name="i-heroicons-map-pin"
        class="w-3 h-3 text-gray-600"
      />
      <span>KNMI · Groningen Eelde</span>
    </div>

    <UButton
      icon="i-heroicons-academic-cap"
      label="Tutorial"
      size="sm"
      color="neutral"
      variant="ghost"
      @click="$emit('open-tutorial')"
    />

    <UButton
      icon="i-heroicons-book-open"
      label="How it works"
      size="sm"
      color="neutral"
      variant="ghost"
      @click="$emit('open-how-it-works')"
    />

    <UButton
      :icon="colorMode.value === 'dark' ? 'i-heroicons-sun' : 'i-heroicons-moon'"
      size="sm"
      color="neutral"
      variant="ghost"
      title="Toggle light/dark mode"
      @click="colorMode.value = colorMode.value === 'dark' ? 'light' : 'dark'"
    />

    <UButton
      icon="i-heroicons-cloud-arrow-up"
      color="primary"
      :label="store.isSaving ? 'Saving…' : 'Save'"
      :loading="store.isSaving"
      :disabled="!canSave"
      size="sm"
      @click="$emit('save')"
    />

    <UDropdownMenu
      :items="exportItems"
      :disabled="!canExport"
    >
      <UButton
        icon="i-heroicons-arrow-down-tray"
        label="Export"
        size="sm"
        color="neutral"
        variant="outline"
        :disabled="!canExport"
        trailing-icon="i-heroicons-chevron-down"
      />
    </UDropdownMenu>
  </div>
</template>

<script setup lang="ts">
import { useSimulationStore } from '~/stores/simulation'
import { useReferentialStore } from '~/stores/referential'
import { useHistoryStore } from '~/stores/history'

defineProps<{
  canSave: boolean
  canExport: boolean
}>()

const emit = defineEmits<{
  'toggle-sidebar': []
  'save': []
  'export': []
  'export-csv': []
  'export-pdf': []
  'open-how-it-works': []
  'open-tutorial': []
}>()

const store = useSimulationStore()
const referential = useReferentialStore()
const _history = useHistoryStore()
const colorMode = useColorMode()

const exportItems = [
  [
    { label: 'Scenario (JSON)', icon: 'i-heroicons-document-text', onSelect: () => emit('export') },
    { label: 'Results (CSV)', icon: 'i-heroicons-table-cells', onSelect: () => emit('export-csv') },
    { label: 'Report (PDF)', icon: 'i-heroicons-document', onSelect: () => emit('export-pdf') }
  ]
]
</script>
