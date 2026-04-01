<template>
  <div class="flex-1 overflow-y-auto p-6 bg-[#020617]">

    <!-- Banner backend indisponible -->
    <div
      v-if="referential.backendAvailable === false"
      class="mb-4 px-4 py-3 bg-amber-900/30 border border-amber-600 rounded-lg text-amber-400 text-sm flex items-center gap-2"
    >
      <span>⚠</span>
      <span>Backend unavailable — Start the API server to enable live simulations.</span>
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
    <div class="mb-6 p-4 bg-[#0F172A] rounded-xl border border-[#1E293B] flex items-center gap-3">
      <UButton
        icon="i-heroicons-plus-circle"
        label="New Scenario"
        size="sm"
        color="primary"
        variant="outline"
        @click="sim.clearScenario(); history.selectedSimulationId = null; selectedScenario = ''"
      />
      <USelect
        v-if="history.simulationHistory.length > 0"
        v-model="selectedScenario"
        :items="scenarioOptions"
        class="flex-1 max-w-xl"
        placeholder="Load a past scenario..."
      />
      <span v-else class="text-sm text-gray-500 flex-1">No past scenarios yet — run your first simulation.</span>
      <UButton
        v-if="selectedScenario"
        icon="i-heroicons-pencil-square"
        size="sm"
        color="neutral"
        variant="ghost"
        title="Rename scenario"
        @click="openRenameModal"
      />
    </div>

    <!-- ── Simulation en cours : skeletons ── -->
    <template v-if="sim.isRunning">
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div v-for="i in 4" :key="i" class="bg-[#0F172A] p-6 rounded-xl border border-[#1E293B]">
          <div class="h-4 bg-gray-700/50 rounded animate-pulse w-24 mb-3" />
          <div class="h-9 bg-gray-700/50 rounded animate-pulse w-32" />
        </div>
      </div>
      <div class="bg-[#0F172A] rounded-xl border border-[#1E293B] p-8">
        <div class="h-6 bg-gray-700/50 rounded animate-pulse w-48 mb-6" />
        <div class="h-80 bg-gray-700/30 rounded-lg animate-pulse" />
      </div>
    </template>

    <!-- ── Résultat disponible ── -->
    <template v-else-if="result">

      <!-- Simulation en erreur -->
      <div v-if="result.status === 'error'" class="mb-6 p-5 bg-red-900/20 border border-red-700 rounded-xl flex items-start gap-3">
        <span class="text-red-400 text-xl">✗</span>
        <div>
          <p class="font-semibold text-red-300">Infeasible simulation</p>
          <p class="text-sm text-red-400/80 mt-1">
            The PyPSA optimization did not find a solution with the selected assets.
            Ensure that the production capacity covers the demand.
          </p>
        </div>
      </div>

      <!-- KPIs fixes -->
      <section class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div class="bg-[#0F172A] p-5 rounded-xl border border-[#1E293B]">
          <p class="text-xs text-gray-400 uppercase tracking-wider mb-2">Status</p>
          <span
            class="text-lg font-bold px-2 py-0.5 rounded"
            :class="result.status === 'optimal' ? 'text-emerald-400' : 'text-red-400'"
          >
            {{ result.status === 'optimal' ? 'Optimal' : 'Infeasible' }}
          </span>
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

        <div class="bg-[#0F172A] p-5 rounded-xl border border-[#1E293B]">
          <p class="text-xs text-gray-400 uppercase tracking-wider mb-2">Power Balance</p>
          <p class="text-2xl font-bold" :class="balanceColor">
            {{ result.status === 'error' ? '—' : formatVal(result.balance_mwh) }}
          </p>
          <p class="text-xs text-gray-500 mt-1">MWh</p>
        </div>
      </section>

      <!-- KPIs dynamiques : capacity factors -->
      <section v-if="capacityFactors.length > 0" class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div
          v-for="{ name, cf, color } in capacityFactors"
          :key="name"
          class="bg-[#0F172A] p-5 rounded-xl border border-[#1E293B]"
        >
          <p class="text-xs text-gray-400 uppercase tracking-wider mb-1 truncate" :title="name">
            {{ generatorEmoji(name) }} {{ name }}
          </p>
          <p class="text-xs text-gray-500 mb-2">Capacity Factor</p>
          <p class="text-2xl font-bold text-white mb-2">{{ (cf * 100).toFixed(1) }}%</p>
          <div class="w-full bg-gray-700 rounded-full h-2">
            <div
              class="h-2 rounded-full transition-all duration-700"
              :style="{ width: (cf * 100) + '%', backgroundColor: color }"
            />
          </div>
        </div>
      </section>

      <!-- Charts (seulement si optimal et données dispo) -->
      <template v-if="result.status === 'optimal' && hasChartData">

        <!-- Chart Production -->
        <div class="bg-[#0F172A] rounded-xl border border-[#1E293B] p-6 mb-6">
          <h2 class="text-lg font-semibold text-white mb-4">Production by generator (MW)</h2>
          <div class="h-72">
            <Line :data="productionChartData" :options="chartOptions" />
          </div>
        </div>

        <!-- Chart Consommation -->
        <div v-if="consumptionChartData.datasets.length" class="bg-[#0F172A] rounded-xl border border-[#1E293B] p-6 mb-6">
          <h2 class="text-lg font-semibold text-white mb-4">Consumption by load (MW)</h2>
          <div class="h-72">
            <Line :data="consumptionChartData" :options="chartOptions" />
          </div>
        </div>
      </template>

      <!-- Placeholder charts si erreur -->
      <div v-else-if="result.status === 'error'" class="bg-[#0F172A] rounded-xl border border-[#1E293B] p-8 mb-6 flex items-center justify-center h-48 text-gray-600">
        No production data — infeasible simulation
      </div>

      <!-- Simulation Summary -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-[#0F172A] p-6 rounded-xl border border-[#1E293B]">
          <h3 class="text-base font-semibold mb-4 text-white">Simulation Summary</h3>
          <div class="space-y-2.5 text-sm">
            <div class="flex justify-between">
              <span class="text-gray-400">ID</span>
              <span class="font-mono text-gray-200">{{ result.id.slice(-8) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-400">Status</span>
              <span class="font-semibold" :class="result.status === 'optimal' ? 'text-emerald-400' : 'text-red-400'">
                {{ result.status === 'optimal' ? 'Optimal' : 'Infeasible' }}
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-400">Supply</span>
              <span class="text-white">{{ result.status === 'error' ? '—' : formatVal(result.total_supply_mwh) + ' MWh' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-400">Demand</span>
              <span class="text-white">{{ result.status === 'error' ? '—' : formatVal(result.total_demand_mwh) + ' MWh' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-400">Balance</span>
              <span :class="balanceColor">{{ result.status === 'error' ? '—' : formatVal(result.balance_mwh) + ' MWh' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-400">Created at</span>
              <span class="font-mono text-gray-300 text-xs">{{ new Date(result.created_at).toLocaleString() }}</span>
            </div>
          </div>
        </div>

        <div class="bg-[#0F172A] p-6 rounded-xl border border-[#1E293B]">
          <h3 class="text-base font-semibold mb-4 text-white">Capacity Factors</h3>
          <div v-if="capacityFactors.length" class="space-y-3">
            <div v-for="{ name, cf } in capacityFactors" :key="name" class="flex justify-between text-sm">
              <span class="text-gray-400 truncate mr-2">{{ generatorEmoji(name) }} {{ name }}</span>
              <span class="font-mono text-white shrink-0">{{ (cf * 100).toFixed(1) }}%</span>
            </div>
          </div>
          <p v-else class="text-gray-600 text-sm">No data</p>
        </div>
      </div>
    </template>

    <!-- ── État vide ── -->
    <div v-else class="flex flex-col items-center justify-center h-96 text-gray-500 gap-3">
      <p class="text-lg">Select assets in the sidebar and click ▶ Play</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import { fetchScenarioExport } from '~/composables/api'
import { useSimulationStore } from '~/stores/simulation'
import { useReferentialStore } from '~/stores/referential'
import { useHistoryStore } from '~/stores/history'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const sim = useSimulationStore()
const referential = useReferentialStore()
const history = useHistoryStore()

// ─── Palette de couleurs ──────────────────────────────────────────────────────

const PALETTE = [
  '#3C83F8', '#10B981', '#F59E0B', '#EF4444',
  '#8B5CF6', '#06B6D4', '#F97316', '#84CC16',
]

function generatorColor(name: string, index: number): string {
  const n = name.toLowerCase()
  if (n.includes('wind')) return '#3C83F8'
  if (n.includes('solar') || n.includes('pv')) return '#F59E0B'
  if (n.includes('nuclear')) return '#8B5CF6'
  return PALETTE[index % PALETTE.length]
}

function generatorEmoji(name: string): string {
  const n = name.toLowerCase()
  if (n.includes('wind')) return '💨'
  if (n.includes('solar') || n.includes('pv')) return '☀️'
  if (n.includes('nuclear')) return '☢️'
  if (n.includes('house') || n.includes('residential')) return '🏠'
  if (n.includes('ev') || n.includes('vehicle')) return '🚗'
  if (n.includes('cable')) return '🔌'
  if (n.includes('transformer')) return '⚙️'
  return '⚡'
}

// ─── Sélecteur de scénario ────────────────────────────────────────────────────

const selectedScenario = ref('')
const loadingScenario = ref(false)

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
  }
  finally {
    isRenaming.value = false
  }
}

const scenarioOptions = computed(() =>
  history.simulationHistory.map((s, i) => ({
    label: s.name
      ? `${s.name} — ${new Date(s.created_at).toLocaleString()} — ${s.status}`
      : `Simulation #${i + 1} — ${new Date(s.created_at).toLocaleString()} — ${s.status}`,
    value: `api-${s.id}`,
  }))
)

watch(selectedScenario, async (val) => {
  if (!val) return
  const id = val.replace('api-', '')
  loadingScenario.value = true
  try {
    const entry = history.simulationHistory.find(s => s.id === id)
    await history.loadSimulationById(id)
    const exported = await fetchScenarioExport(id)
    sim.loadFromScenario(exported, entry?.name ?? '')
  }
  finally {
    loadingScenario.value = false
  }
})

// ─── Résultat courant ─────────────────────────────────────────────────────────

const result = computed(() => history.currentResult)

// ─── KPIs dynamiques ─────────────────────────────────────────────────────────

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

// ─── Charts dynamiques ────────────────────────────────────────────────────────

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
    legend: { labels: { color: '#94A3B8', font: { size: 12 }, padding: 16, boxWidth: 12 } },
    tooltip: { backgroundColor: '#0F172A', titleColor: '#E2E8F0', bodyColor: '#94A3B8' },
  },
  scales: {
    x: { ticks: { color: '#64748B', font: { size: 10 }, maxTicksLimit: 24 }, grid: { color: '#1E293B' } },
    y: {
      beginAtZero: true,
      ticks: { color: '#64748B', font: { size: 10 } },
      grid: { color: '#1E293B' },
      title: { display: true, text: 'MW', color: '#64748B', font: { size: 11 } },
    },
  },
}

// ─── Formatters ───────────────────────────────────────────────────────────────

const formatVal = (v: number | null | undefined) =>
  v == null ? '—' : v.toFixed(2)

// ─── Init ─────────────────────────────────────────────────────────────────────

onMounted(async () => {
  await referential.loadReferential()
  if (referential.backendAvailable) {
    await history.loadHistory()
  }
})
</script>
