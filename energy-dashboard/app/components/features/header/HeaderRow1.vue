<template>
  <nav
    aria-label="Main toolbar"
    class="flex items-center gap-2 px-4 h-14"
  >
    <UButton
      variant="ghost"
      icon="i-heroicons-bars-3"
      color="neutral"
      aria-label="Toggle sidebar"
      @click="$emit('toggle-sidebar')"
    />

    <img
      src="/logo.png"
      alt="EnergyDash"
      class="h-8 w-auto"
    >

    <span class="font-semibold text-base text-gray-900 dark:text-white hidden sm:block">
      {{ $t('header.appTitle') }}
    </span>

    <!-- Backend status badge -->
    <span
      class="text-xs px-2 py-1 rounded-full ml-2"
      :class="referential.backendAvailable === true
        ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-400'
        : referential.backendAvailable === false
          ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400'
          : 'bg-gray-200 text-gray-500 dark:bg-gray-800 dark:text-gray-300'"
    >
      {{ referential.backendAvailable === true ? `● ${$t('header.connected')}` : referential.backendAvailable === false ? `● ${$t('header.offline')}` : '● …' }}
    </span>

    <div class="flex-1" />

    <!-- Weather station indicator -->
    <div
      class="hidden sm:flex items-center gap-1 text-xs text-gray-500 dark:text-gray-300 border border-gray-200 dark:border-slate-800 rounded px-2 h-6 shrink-0"
      title="Weather data source: KNMI station 06280 — Groningen Eelde. Covers Jan 2025 → Dec 2025."
    >
      <UIcon
        name="i-heroicons-map-pin"
        class="w-3 h-3 text-gray-600 dark:text-gray-300"
        aria-hidden="true"
      />
      <span>KNMI · Groningen Eelde</span>
    </div>

    <UButton
      icon="i-heroicons-academic-cap"
      :label="$t('header.tutorial')"
      size="sm"
      color="neutral"
      variant="ghost"
      @click="$emit('open-tutorial')"
    />

    <UButton
      icon="i-heroicons-book-open"
      :label="$t('header.howItWorks')"
      size="sm"
      color="neutral"
      variant="ghost"
      @click="$emit('open-how-it-works')"
    />

    <!-- Language switcher -->
    <UButton
      icon="i-heroicons-language"
      size="sm"
      color="neutral"
      variant="ghost"
      :title="$t('header.language')"
      aria-label="Switch language"
      @click="toggleLocale"
    >
      <span class="text-xs font-semibold">{{ locale === 'en' ? 'FR' : 'EN' }}</span>
    </UButton>

    <UButton
      :icon="colorMode.value === 'dark' ? 'i-heroicons-sun' : 'i-heroicons-moon'"
      size="sm"
      color="neutral"
      variant="ghost"
      :title="$t('header.toggleDarkMode')"
      aria-label="Toggle dark mode"
      @click="colorMode.value = colorMode.value === 'dark' ? 'light' : 'dark'"
    />

    <UButton
      icon="i-heroicons-cloud-arrow-up"
      color="primary"
      :label="store.isSaving ? $t('header.saving') : $t('header.save')"
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
        :label="$t('header.export')"
        size="sm"
        color="neutral"
        variant="outline"
        :disabled="!canExport"
        trailing-icon="i-heroicons-chevron-down"
      />
    </UDropdownMenu>
  </nav>
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
const { t, locale, setLocale } = useI18n()

function toggleLocale() {
  setLocale(locale.value === 'en' ? 'fr' : 'en')
}

const exportItems = computed(() => [
  [
    { label: t('header.exportScenarioJson'), icon: 'i-heroicons-document-text', onSelect: () => emit('export') },
    { label: t('header.exportResultsCsv'), icon: 'i-heroicons-table-cells', onSelect: () => emit('export-csv') },
    { label: t('header.exportReportPdf'), icon: 'i-heroicons-document', onSelect: () => emit('export-pdf') }
  ]
])
</script>
