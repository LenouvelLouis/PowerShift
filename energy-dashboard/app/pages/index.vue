<template>
  <div class="flex flex-col min-h-full bg-[#020617] p-6 gap-6">

    <!-- Backend unavailable banner -->
    <div
      v-if="referential.backendAvailable === false"
      class="px-4 py-3 bg-amber-900/30 border border-amber-600/60 rounded-lg text-amber-400 text-sm flex items-center gap-2"
    >
      <span>⚠</span>
      <span>Backend unavailable — start the API server to enable live simulations.</span>
    </div>

    <!-- Rename scenario modal -->
    <UModal v-model:open="showRenameModal">
      <template #header>
        <h3 class="font-semibold text-white">Rename scenario</h3>
      </template>
      <template #body>
        <UInput
          v-model="renameDraft"
          placeholder="Scenario name"
          autofocus
          @keyup.enter="confirmRename"
        />
      </template>
      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton label="Cancel" color="neutral" variant="ghost" @click="renameTarget = null" />
          <UButton
            label="Rename"
            color="primary"
            :loading="isRenaming"
            :disabled="!renameDraft.trim()"
            @click="confirmRename"
          />
        </div>
      </template>
    </UModal>

    <!-- Scenario bar -->
    <div class="group p-4 bg-[#0F172A] rounded-xl border border-[#1E293B] flex items-center gap-3">
      <UButton
        icon="i-heroicons-plus-circle"
        label="New Scenario"
        size="sm"
        color="primary"
        variant="outline"
        :disabled="loadingScenario || historyLoading"
        @click="sim.clearScenario(); sim.selectedHistoryId = null; history.selectedSimulationId = null"
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
        :disabled="loadingScenario || historyLoading"
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
      <span v-else class="text-sm text-gray-500 flex-1">No past scenarios yet — run your first simulation.</span>
      <UButton
        v-if="selectedScenario"
        icon="i-heroicons-pencil-square"
        size="sm"
        color="neutral"
        variant="ghost"
        title="Rename scenario"
        :disabled="loadingScenario"
        @click="openRenameModal"
      />
      <!-- Live indicator -->
      <span v-if="sim.isLiveMode" class="flex items-center gap-1.5 text-xs text-emerald-500 shrink-0">
        <span class="inline-block h-1.5 w-1.5 rounded-full bg-emerald-400" :class="sim.isLiveRunning ? 'animate-pulse' : ''" />
        {{ sim.isLiveRunning ? 'Computing…' : 'Live' }}
      </span>
      <span v-else-if="sim.displayedResult" class="text-xs text-gray-500 shrink-0">
        {{ new Date(sim.displayedResult.created_at).toLocaleString() }}
      </span>
    </div>

    <!-- Loading a past scenario: shimmer -->
    <template v-if="loadingScenario">
      <div class="relative overflow-hidden bg-[#0F172A] rounded-xl border border-[#1E293B] p-8">
        <div class="absolute inset-0 bg-gradient-to-r from-transparent via-[#334155]/30 to-transparent -translate-x-full animate-[shimmer_1.4s_infinite]" />
        <div class="relative">
          <div class="flex items-center gap-3 mb-6">
            <div class="h-8 w-8 rounded-full border-2 border-[#3C83F8]/60 border-t-[#7DD3FC] animate-spin" />
            <div>
              <p class="text-white font-semibold">Preparing your scenario</p>
              <p class="text-sm text-gray-400">Restoring KPIs, charts, and simulation context...</p>
            </div>
          </div>
          <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div v-for="i in 4" :key="`kpi-${i}`" class="bg-[#020617] p-5 rounded-xl border border-[#1E293B]">
              <div class="h-3 w-20 rounded bg-slate-700/50 mb-3" />
              <div class="h-8 w-28 rounded bg-slate-700/40" />
            </div>
          </div>
          <div class="bg-[#020617] rounded-xl border border-[#1E293B] p-6">
            <div class="h-5 w-48 rounded bg-slate-700/50 mb-4" />
            <div class="h-64 rounded-lg bg-slate-700/30" />
          </div>
        </div>
      </div>
    </template>

    <!-- Running: skeleton -->
    <template v-else-if="sim.isLiveRunning || sim.isRunning">
      <div class="relative overflow-hidden bg-[#0F172A] rounded-xl border border-[#1E293B] p-8">
        <div class="absolute inset-0 bg-gradient-to-r from-transparent via-[#334155]/30 to-transparent -translate-x-full animate-[shimmer_1.4s_infinite]" />
        <div class="relative">
          <div class="flex items-center gap-3 mb-6">
            <div class="h-8 w-8 rounded-full border-2 border-[#3C83F8]/60 border-t-[#7DD3FC] animate-spin" />
            <div>
              <p class="text-white font-semibold">Optimising your scenario</p>
              <p class="text-sm text-gray-400">Running the simulation, results coming shortly...</p>
            </div>
          </div>
          <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div v-for="i in 4" :key="`kpi-${i}`" class="bg-[#020617] p-5 rounded-xl border border-[#1E293B]">
              <div class="h-3 w-20 rounded bg-slate-700/50 mb-3" />
              <div class="h-8 w-28 rounded bg-slate-700/40" />
            </div>
          </div>
          <div class="bg-[#020617] rounded-xl border border-[#1E293B] p-6">
            <div class="h-5 w-48 rounded bg-slate-700/50 mb-4" />
            <div class="h-64 rounded-lg bg-slate-700/30" />
          </div>
        </div>
      </div>
    </template>

    <!-- Result available -->
    <template v-else-if="result">

      <!-- Error banner -->
      <div
        v-if="result.status === 'error' || result.status === 'infeasible'"
        class="px-5 py-4 bg-red-900/20 border border-red-700/60 rounded-xl flex items-start gap-3"
      >
        <span class="text-red-400 text-xl leading-none mt-0.5">✗</span>
        <div>
          <p class="font-semibold text-red-300">{{ errorHeadline }}</p>
          <p class="text-sm text-red-400/80 mt-1">{{ errorDescription }}</p>
        </div>
      </div>

      <!-- Two-column layout -->
      <div class="grid grid-cols-1 xl:grid-cols-2 gap-6 items-start">

        <!-- ── LEFT column: KPIs + summary + capacity factors ── -->
        <div class="flex flex-col gap-6">

          <!-- KPI cards 2×2 -->
          <div class="grid grid-cols-2 gap-4">
            <div class="bg-[#0F172A] p-5 rounded-xl border border-[#1E293B]">
              <p class="text-xs text-gray-400 uppercase tracking-wider mb-2">Status</p>
              <span class="text-xl font-bold" :class="result.status === 'optimal' ? 'text-emerald-400' : 'text-red-400'">
                {{ result.status === 'optimal' ? 'Optimal' : 'Infeasible' }}
              </span>
            </div>
            <div class="bg-[#0F172A] p-5 rounded-xl border border-[#1E293B]">
              <p class="text-xs text-gray-400 uppercase tracking-wider mb-2">Power Balance</p>
              <p class="text-2xl font-bold" :class="balanceColor">
                {{ result.status === 'error' ? '—' : formatVal(result.balance_mwh) }}
              </p>
              <p class="text-xs text-gray-500 mt-1">MWh</p>
            </div>
            <div class="bg-[#0F172A] p-5 rounded-xl border border-[#1E293B]">
              <p class="text-xs text-gray-400 uppercase tracking-wider mb-2">Total Supply</p>
              <p class="text-2xl font-bold text-white">
                {{ result.status === 'error' ? '—' : formatVal(result.total_supply_mwh) }}
              </p>
              <p class="text-xs text-gray-500 mt-1">MWh</p>
            </div>
            <div class="bg-[#0F172A] p-5 rounded-xl border border-[#1E293B]">
              <p class="text-xs text-gray-400 uppercase tracking-wider mb-2">Total Demand</p>
              <p class="text-2xl font-bold text-white">
                {{ result.status === 'error' ? '—' : formatVal(result.total_demand_mwh) }}
              </p>
              <p class="text-xs text-gray-500 mt-1">MWh</p>
            </div>
          </div>

          <!-- Simulation summary table -->
          <div class="bg-[#0F172A] rounded-xl border border-[#1E293B] p-5">
            <h3 class="text-sm font-semibold text-white uppercase tracking-wider mb-4">Simulation Summary</h3>
            <div class="space-y-2.5 text-sm">
              <div class="flex justify-between items-center">
                <span class="text-gray-400">ID</span>
                <span class="font-mono text-gray-300 text-xs">{{ result.id.slice(-8) }}</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-gray-400">Status</span>
                <span class="font-semibold" :class="result.status === 'optimal' ? 'text-emerald-400' : 'text-red-400'">
                  {{ result.status === 'optimal' ? 'Optimal' : 'Infeasible' }}
                </span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-gray-400">Supply</span>
                <span class="text-white font-mono">{{ result.status === 'error' ? '—' : `${formatVal(result.total_supply_mwh)} MWh` }}</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-gray-400">Demand</span>
                <span class="text-white font-mono">{{ result.status === 'error' ? '—' : `${formatVal(result.total_demand_mwh)} MWh` }}</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-gray-400">Balance</span>
                <span class="font-mono" :class="balanceColor">{{ result.status === 'error' ? '—' : `${formatVal(result.balance_mwh)} MWh` }}</span>
              </div>
              <div class="flex justify-between items-center border-t border-[#1E293B] pt-2.5 mt-1">
                <span class="text-gray-400">Created</span>
                <span class="font-mono text-gray-300 text-xs">{{ new Date(result.created_at).toLocaleString() }}</span>
              </div>
            </div>
          </div>

          <!-- Capacity factors -->
          <div v-if="capacityFactors.length" class="bg-[#0F172A] rounded-xl border border-[#1E293B] p-5">
            <h3 class="text-sm font-semibold text-white uppercase tracking-wider mb-4">Capacity Factors</h3>
            <div class="space-y-3">
              <div v-for="{ name, cf, color } in capacityFactors" :key="name">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-xs text-gray-400 truncate mr-2 flex items-center gap-1" :title="name">
                    <UIcon :name="generatorIcon(name)" class="w-3 h-3 shrink-0" />
                    {{ name }}
                  </span>
                  <span class="font-mono text-white text-xs shrink-0">{{ (cf * 100).toFixed(1) }}%</span>
                </div>
                <div class="w-full bg-[#1E293B] rounded-full h-1.5">
                  <div
                    class="h-1.5 rounded-full transition-all duration-700"
                    :style="{ width: `${Math.min(cf * 100, 100)}%`, backgroundColor: color }"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ── RIGHT column: charts ── -->
        <div class="flex flex-col gap-6">
          <template v-if="result.status === 'optimal' && hasChartData">

            <!-- Production chart -->
            <div class="bg-[#0F172A] rounded-xl border border-[#1E293B] p-5">
              <div class="flex items-center justify-between mb-4">
                <h2 class="text-sm font-semibold text-white uppercase tracking-wider">Production by Generator</h2>
                <span class="text-xs text-gray-500">MW</span>
              </div>
              <div class="h-72">
                <Line :data="productionChartData" :options="chartOptions" />
              </div>
            </div>

            <!-- Consumption chart -->
            <div v-if="consumptionChartData.datasets.length" class="bg-[#0F172A] rounded-xl border border-[#1E293B] p-5">
              <div class="flex items-center justify-between mb-4">
                <h2 class="text-sm font-semibold text-white uppercase tracking-wider">Consumption by Load</h2>
                <span class="text-xs text-gray-500">MW</span>
              </div>
              <div class="h-72">
                <Line :data="consumptionChartData" :options="chartOptions" />
              </div>
            </div>
          </template>

          <!-- No chart data: infeasible or empty -->
          <div
            v-else
            class="bg-[#0F172A] rounded-xl border border-[#1E293B] p-8 flex items-center justify-center h-72 text-gray-600 text-sm"
          >
            {{ result.status === 'error' ? 'No production data — infeasible simulation' : 'No time-series data available' }}
          </div>
        </div>
      </div>
    </template>

    <!-- Empty state -->
    <div v-else class="flex flex-col items-center justify-center flex-1 min-h-96 text-gray-500 gap-3">
      <UIcon name="i-heroicons-bolt" class="w-12 h-12 text-gray-700" />
      <p class="text-base">Select supply and demand assets in the sidebar</p>
      <p class="text-xs text-gray-600">Simulation runs automatically · use <strong class="text-gray-400">Save</strong> to persist results</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Title,
  Tooltip,
} from 'chart.js'
import { computed, onMounted, ref, shallowRef, watch } from 'vue'
import { Line } from 'vue-chartjs'
import { fetchScenarioExport } from '~/composables/api'
import { useHistoryStore } from '~/stores/history'
import { useReferentialStore } from '~/stores/referential'
import { useSimulationStore } from '~/stores/simulation'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const sim = useSimulationStore()
const referential = useReferentialStore()
const history = useHistoryStore()

// ─── Color palette ─────────────────────────────────────────────────────────────

const PALETTE = ['#3C83F8', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#F97316', '#84CC16']

function generatorColor(name: string, index: number): string {
  const n = name.toLowerCase()
  if (n.includes('wind')) return '#3C83F8'
  if (n.includes('solar') || n.includes('pv')) return '#F59E0B'
  if (n.includes('nuclear')) return '#8B5CF6'
  return PALETTE[index % PALETTE.length]
}

function generatorIcon(name: string): string {
  const n = name.toLowerCase()
  if (n.includes('wind')) return 'i-heroicons-arrow-path'
  if (n.includes('solar') || n.includes('pv')) return 'i-heroicons-sun'
  if (n.includes('nuclear')) return 'i-heroicons-bolt'
  if (n.includes('house') || n.includes('residential')) return 'i-heroicons-home'
  if (n.includes('ev') || n.includes('vehicle')) return 'i-heroicons-truck'
  if (n.includes('cable')) return 'i-heroicons-link'
  if (n.includes('transformer')) return 'i-heroicons-cpu-chip'
  return 'i-heroicons-bolt'
}

// ─── Scenario selector ─────────────────────────────────────────────────────────

const loadingScenario = ref(false)
const historyLoading = ref(true)

// Two-way binding to store — empty string = live mode, 'api-{uuid}' = saved sim
const selectedScenario = computed({
  get() {
    return sim.selectedHistoryId ? `api-${sim.selectedHistoryId}` : ''
  },
  set(val: string) {
    sim.selectedHistoryId = val ? val.replace('api-', '') : null
  },
})

// When user picks a saved sim: load result + restore scenario in sidebar
watch(selectedScenario, async (val) => {
  if (!val) return
  const id = val.replace('api-', '')
  // Skip reload if this sim was just saved and is already the reference
  if (sim.referenceSimId === id && history.currentResult?.id === id) return
  loadingScenario.value = true
  try {
    const entry = history.simulationHistory.find(s => s.id === id)
    await history.loadSimulationById(id)
    const exported = await fetchScenarioExport(id)
    sim.loadFromScenario(exported, entry?.name ?? '')
    // Set as reference so Save is disabled until params change
    sim.setReference(id, sim.buildPayload())
  } finally {
    loadingScenario.value = false
  }
})

// ─── Rename scenario ──────────────────────────────────────────────────────────

const renameTarget = ref<{ id: string } | null>(null)
const renameDraft = ref('')
const isRenaming = ref(false)

const showRenameModal = computed({
  get: () => renameTarget.value !== null,
  set: (val: boolean) => { if (!val) renameTarget.value = null },
})

const openRenameModal = () => {
  const current = history.simulationHistory.find(s => `api-${s.id}` === selectedScenario.value)
  if (!current) return
  renameTarget.value = { id: current.id }
  renameDraft.value = current.name ?? ''
}

const confirmRename = async () => {
  if (!renameTarget.value || !renameDraft.value.trim()) return
  isRenaming.value = true
  try {
    await history.renameEntry(renameTarget.value.id, renameDraft.value.trim())
    renameTarget.value = null
  } finally {
    isRenaming.value = false
  }
}

// ─── Scenario options ─────────────────────────────────────────────────────────

const scenarioDateFormatter = new Intl.DateTimeFormat(undefined, { day: '2-digit', month: '2-digit', year: 'numeric' })
const scenarioDateTimeFormatter = new Intl.DateTimeFormat(undefined, { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' })

type ScenarioOption = { label: string; value: string; dateShort: string; dateFull: string; searchText: string }

const SCENARIO_MENU_LIMIT = 160
const scenarioAllOptions = shallowRef<ScenarioOption[]>([])

watch(
  () => history.simulationHistory,
  (rows) => {
    scenarioAllOptions.value = rows.map((s, i) => {
      const createdAt = new Date(s.created_at)
      const label = s.name
        ? `${s.name} · ${s.status} · ${s.solver.toUpperCase()}`
        : `#${i + 1} · ${s.status} · ${s.solver.toUpperCase()}`
      return {
        label,
        value: `api-${s.id}`,
        dateShort: scenarioDateFormatter.format(createdAt),
        dateFull: scenarioDateTimeFormatter.format(createdAt),
        searchText: `${label} ${s.name ?? ''} ${s.status} ${s.solver} ${s.id}`.toLowerCase(),
      }
    })
  },
  { immediate: true, deep: true },
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

// ─── Current result ────────────────────────────────────────────────────────────

const result = computed(() => sim.displayedResult)

const errorHeadline = computed(() => {
  const status = result.value?.status
  if (status !== 'error' && status !== 'infeasible') return 'Simulation error'
  if (status === 'infeasible') return 'Simulation infaisable'
  if (result.value?.result_json?.error_type === 'solver_error') return 'Solver unavailable'
  return 'Simulation error'
})

const errorDescription = computed(() => {
  const status = result.value?.status
  if (status !== 'error' && status !== 'infeasible') return ''
  const details = result.value?.result_json?.error
  if (status === 'infeasible') {
    return details ?? "L'optimisation PyPSA n'a pas trouvé de solution avec les assets sélectionnés. Vérifiez que la capacité de production couvre la demande."
  }
  if (result.value?.result_json?.error_type === 'solver_error') {
    const solver = result.value.result_json?.solver ?? 'selected solver'
    return details
      ? `The solver '${solver}' is unavailable or misconfigured. ${details}`
      : `The solver '${solver}' is unavailable or misconfigured on the backend.`
  }
  return details ?? 'The optimization failed. Ensure production can cover demand and try again.'
})

// ─── KPIs ──────────────────────────────────────────────────────────────────────

const capacityFactors = computed(() => {
  const cf = result.value?.result_json?.capacity_factors ?? {}
  return Object.entries(cf).map(([name, value], i) => ({
    name,
    cf: value as number,
    color: generatorColor(name, i),
  }))
})

const balanceColor = computed(() => {
  const b = result.value?.balance_mwh ?? 0
  if (result.value?.status === 'error') return 'text-gray-500'
  if (Math.abs(b) < 0.001) return 'text-emerald-400'
  return b > 0 ? 'text-blue-400' : 'text-red-400'
})

// ─── Chart data ────────────────────────────────────────────────────────────────

const generatorsT = computed(() => result.value?.result_json?.generators_t ?? {})
const loadsT = computed(() => result.value?.result_json?.loads_t ?? {})
const hasChartData = computed(() => Object.keys(generatorsT.value).length > 0)

const timeLabels = computed(() => {
  const firstGen = Object.values(generatorsT.value)[0]
  const n = firstGen?.p?.length ?? 0
  return Array.from({ length: n }, (_, i) => `H${i}`)
})

const productionChartData = computed(() => ({
  labels: timeLabels.value,
  datasets: Object.entries(generatorsT.value).map(([name, data], i) => ({
    label: name,
    data: (data as { p: number[] }).p,
    borderColor: generatorColor(name, i),
    backgroundColor: generatorColor(name, i) + '26',
    fill: false,
    tension: 0.4,
    pointRadius: timeLabels.value.length > 48 ? 0 : 2,
    pointHoverRadius: 5,
    borderWidth: 2,
  })),
}))

const consumptionChartData = computed(() => ({
  labels: timeLabels.value,
  datasets: Object.entries(loadsT.value).map(([name, data], i) => ({
    label: name,
    data: (data as { p: number[] }).p,
    borderColor: PALETTE[(i + 4) % PALETTE.length],
    backgroundColor: PALETTE[(i + 4) % PALETTE.length] + '26',
    fill: false,
    tension: 0.4,
    pointRadius: timeLabels.value.length > 48 ? 0 : 2,
    pointHoverRadius: 5,
    borderWidth: 2,
  })),
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index' as const, intersect: false },
  plugins: {
    legend: {
      labels: { color: '#94A3B8', font: { size: 11 }, padding: 12, boxWidth: 10 },
    },
    tooltip: {
      backgroundColor: '#0F172A',
      titleColor: '#E2E8F0',
      bodyColor: '#94A3B8',
      borderColor: '#1E293B',
      borderWidth: 1,
    },
  },
  scales: {
    x: {
      ticks: { color: '#64748B', font: { size: 10 }, maxTicksLimit: 24 },
      grid: { color: '#1E293B' },
    },
    y: {
      beginAtZero: true,
      ticks: { color: '#64748B', font: { size: 10 } },
      grid: { color: '#1E293B' },
      title: { display: true, text: 'MW', color: '#64748B', font: { size: 11 } },
    },
  },
}

// ─── Formatters ────────────────────────────────────────────────────────────────

const formatVal = (v: number | null | undefined) => v == null ? '—' : v.toFixed(2)

// ─── Init ──────────────────────────────────────────────────────────────────────

onMounted(async () => {
  try {
    await referential.loadReferential()
    if (referential.backendAvailable) {
      await history.loadHistory()
      // Do NOT auto-select the latest saved sim — always start in live mode
    }
  } finally {
    historyLoading.value = false
  }
})
</script>

<style scoped>
@keyframes shimmer {
  100% {
    transform: translateX(100%);
  }
}
</style>
