<template>
  <div class="group p-4 bg-[#0F172A] rounded-xl border border-[#1E293B] flex items-center gap-3">
    <RenameScenarioModal
      :open="showRenameModal"
      :initial-name="renameDraft"
      :loading="isRenaming"
      @update:open="(v) => { if (!v) showRenameModal = false }"
      @confirm="confirmRename"
    />

    <UButton
      icon="i-heroicons-plus-circle"
      label="New Scenario"
      size="sm"
      color="primary"
      variant="outline"
      :disabled="loading || historyLoading"
      @click="newScenario"
    />

    <div
      v-if="historyLoading"
      class="flex-1 max-w-xl h-8 rounded-md border border-[#334155] bg-[#0B1220] px-2.5 flex items-center gap-2"
    >
      <div class="h-3.5 w-3.5 rounded-full border-2 border-[#3C83F8]/40 border-t-[#7DD3FC] animate-spin" />
      <span class="text-xs text-slate-300/90">Loading past scenarios...</span>
    </div>

    <USelectMenu
      v-else-if="history.simulationHistory.length > 0"
      v-model="selectedScenario"
      :items="scenarioInitialOptions"
      value-key="value"
      :searchable="searchScenarioOptions"
      class="flex-1 max-w-xl"
      placeholder="Load a past scenario..."
      :disabled="loading || historyLoading"
    >
      <template #item="{ item }">
        <div class="group flex items-center justify-between gap-3 w-full">
          <span class="truncate">{{ item.label }}</span>
          <span
            class="text-xs text-gray-500 opacity-0 transition-opacity group-hover:opacity-100 shrink-0"
            :title="item.dateFull"
          >{{ item.dateShort }}</span>
        </div>
      </template>
    </USelectMenu>

    <span
      v-else
      class="text-sm text-gray-500 flex-1"
    >No past scenarios yet — run your first simulation.</span>

    <UButton
      v-if="selectedScenario"
      icon="i-heroicons-pencil-square"
      size="sm"
      color="neutral"
      variant="ghost"
      title="Rename scenario"
      :disabled="loading"
      @click="openRenameModal"
    />

    <span
      v-if="sim.isLiveMode"
      class="flex items-center gap-1.5 text-xs text-emerald-500 shrink-0"
    >
      <span
        class="inline-block h-1.5 w-1.5 rounded-full bg-emerald-400"
        :class="sim.isLiveRunning ? 'animate-pulse' : ''"
      />
      {{ sim.isLiveRunning ? 'Computing…' : 'Live' }}
    </span>
    <span
      v-else-if="sim.displayedResult"
      class="text-xs text-gray-500 shrink-0"
    >
      {{ new Date(sim.displayedResult.created_at).toLocaleString() }}
    </span>
  </div>
</template>

<script setup lang="ts">
import { fetchScenarioExport, type SimulationListItem } from '~/composables/api'
import { useSimulationStore } from '~/stores/simulation'
import { useHistoryStore } from '~/stores/history'

const emit = defineEmits<{ 'loading-change': [loading: boolean] }>()

const sim = useSimulationStore()
const history = useHistoryStore()

const loading = ref(false)
const historyLoading = ref(true)

watch(loading, val => emit('loading-change', val))

// ─── Scenario selector ─────────────────────────────────────────────────────────

const selectedScenario = computed({
  get() { return sim.selectedHistoryId ? `api-${sim.selectedHistoryId}` : '' },
  set(val: string) { sim.selectedHistoryId = val ? val.replace('api-', '') : null }
})

watch(selectedScenario, async (val) => {
  if (!val) return
  const id = val.replace('api-', '')
  if (sim.referenceSimId === id && history.currentResult?.id === id) return
  loading.value = true
  try {
    const entry = (history.simulationHistory as SimulationListItem[]).find(s => s.id === id)
    await history.loadSimulationById(id)
    const exported = await fetchScenarioExport(id)
    sim.loadFromScenario(exported, entry?.name ?? '')
    sim.setReference(id, sim.buildPayload())
  } finally {
    loading.value = false
  }
})

function newScenario() {
  sim.clearScenario()
  sim.selectedHistoryId = null
  history.selectedSimulationId = null
}

// ─── Rename ────────────────────────────────────────────────────────────────────

const showRenameModal = ref(false)
const renameDraft = ref('')
const isRenaming = ref(false)

function openRenameModal() {
  const current = (history.simulationHistory as SimulationListItem[]).find(s => `api-${s.id}` === selectedScenario.value)
  if (!current) return
  renameDraft.value = current.name ?? ''
  showRenameModal.value = true
}

async function confirmRename(name: string) {
  const current = (history.simulationHistory as SimulationListItem[]).find(s => `api-${s.id}` === selectedScenario.value)
  if (!current) return
  isRenaming.value = true
  try {
    await history.renameEntry(current.id, name)
    showRenameModal.value = false
  } finally {
    isRenaming.value = false
  }
}

// ─── Scenario options ─────────────────────────────────────────────────────────

const scenarioDateFormatter = new Intl.DateTimeFormat(undefined, { day: '2-digit', month: '2-digit', year: 'numeric' })
const scenarioDateTimeFormatter = new Intl.DateTimeFormat(undefined, { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' })
const SCENARIO_MENU_LIMIT = 160

type ScenarioOption = { label: string, value: string, dateShort: string, dateFull: string, searchText: string }
const scenarioAllOptions = shallowRef<ScenarioOption[]>([])

watch(
  () => history.simulationHistory,
  (rows) => {
    scenarioAllOptions.value = (rows as SimulationListItem[]).map((s, i) => {
      const createdAt = new Date(s.created_at)
      const label = s.name
        ? `${s.name} · ${s.status} · ${s.solver.toUpperCase()}`
        : `#${i + 1} · ${s.status} · ${s.solver.toUpperCase()}`
      return {
        label,
        value: `api-${s.id}`,
        dateShort: scenarioDateFormatter.format(createdAt),
        dateFull: scenarioDateTimeFormatter.format(createdAt),
        searchText: `${label} ${s.name ?? ''} ${s.status} ${s.solver} ${s.id}`.toLowerCase()
      }
    })
  },
  { immediate: true, deep: true }
)

const scenarioInitialOptions = computed(() => scenarioAllOptions.value.slice(0, SCENARIO_MENU_LIMIT))

const searchScenarioOptions = (query: string): ScenarioOption[] => {
  const q = query.trim().toLowerCase()
  if (!q) return scenarioInitialOptions.value
  const out: ScenarioOption[] = []
  for (const item of scenarioAllOptions.value) {
    if (item.searchText.includes(q)) {
      out.push(item)
      if (out.length >= SCENARIO_MENU_LIMIT) break
    }
  }
  return out
}

// ─── Init ──────────────────────────────────────────────────────────────────────

onMounted(async () => {
  try {
    const { useReferentialStore } = await import('~/stores/referential')
    const referential = useReferentialStore()
    await referential.loadReferential()
    if (referential.backendAvailable) {
      await history.loadHistory()
    }
  } finally {
    historyLoading.value = false
  }
})
</script>
