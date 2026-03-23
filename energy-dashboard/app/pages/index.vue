<template>
  <!-- UNIQUEMENT le contenu principal pour <NuxtPage /> -->
  <div class="flex-1 overflow-y-auto p-6 bg-[#020617]">
    
    <!-- Sélecteur scénario -->
    <div class="mb-8 p-6 bg-[#0F172A] rounded-xl border border-[#1E293B]">
      <div class="flex items-center gap-4">
        <label class="font-medium text-gray-300">Scénario :</label>
        <!-- TO DO MAKE IT DYNAMIC --> <USelect
          v-model="currentScenario"
          :items="[ 
            { label: 'Scenario 1 (1h)', value: 'scenario1' },
            { label: 'Scenario 2 (24h)', value: 'scenario2' }
          ]"
          class="w-64"
        />
      </div>
    </div>

    <!-- KPIs -->
    <section v-if="result" class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-12">
      <div class="bg-[#0F172A] p-6 rounded-xl border border-[#1E293B]">
        <p class="text-sm font-medium text-gray-400 mb-2">Nuclear Central Utilisation</p>
        <p class="text-3xl font-bold text-white mb-1">{{ usage }}%</p>
        <div class="w-full bg-gray-700 rounded-full h-3">
          <div 
            class="bg-gradient-to-r from-emerald-500 to-emerald-400 h-3 rounded-full transition-all duration-500"
            :style="{ width: usage + '%' }"
          ></div>
        </div>
      </div>

      <div class="bg-[#0F172A] p-6 rounded-xl border border-[#1E293B]">
        <p class="text-sm font-medium text-gray-400 mb-2">Demand Power</p>
        <p class="text-3xl font-bold text-white">{{ formatMwh(totalDemand) }}</p>
      </div>

      <div class="bg-[#0F172A] p-6 rounded-xl border border-[#1E293B]">
        <p class="text-sm font-medium text-gray-400 mb-2">Power Balance</p>
        <p class="text-3xl font-bold text-white">{{ balanceLabel }}</p>
      </div>
    </section>

    <div v-if="result && chartData.labels.length" class="bg-[#0F172A] rounded-xl border border-[#1E293B] p-8">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-2xl font-bold text-white">Nuclear Production (kW)</h2>
        <span class="px-3 py-1 bg-[#3C83F8]/20 text-[#3C83F8] rounded-full text-sm font-medium">
          {{ result.result_json?.capacity_factors?.['Nuclear Plant US03']?.toFixed(1) ?? 'N/A' }} CF
        </span>
      </div>
      <div class="h-[400px]">
        <Line :data="chartData" :options="chartOptions" />
      </div>
    </div>

    <!-- Détails simulation -->
    <div v-if="result" class="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="bg-[#0F172A] p-6 rounded-xl border border-[#1E293B]">
        <h3 class="text-xl font-semibold mb-6 text-white">Simulation Summary</h3>
        <div class="space-y-3 text-sm">
          <div class="flex justify-between">
            <span class="text-gray-400">ID</span>
            <span class="font-mono text-gray-200">{{ result.id.slice(-8) }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-400">Status</span>
            <span class="text-emerald-400 font-semibold">{{ result.status }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-400">Supply</span>
            <span class="font-bold text-white">{{ formatMwh(result.total_supply_mwh) }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-400">Demand</span>
            <span class="font-bold text-white">{{ formatMwh(result.total_demand_mwh) }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-400">Balance</span>
            <span class="font-bold text-emerald-400">{{ result.balance_mwh.toFixed(3) }} kWh</span>
          </div>
        </div>
      </div>

      <div class="bg-[#0F172A] p-6 rounded-xl border border-[#1E293B]">
        <h3 class="text-xl font-semibold mb-6 text-white">Capacités</h3>
        <div class="space-y-3 text-sm">
          <div class="flex justify-between">
            <span>Nuclear (nominal)</span>
            <span class="font-mono">100 kW</span>
          </div>
          <div class="flex justify-between">
            <span>{{ currentScenario === 'scenario1' ? '1 heure' : '24 heures' }}</span>
            <span class="font-mono">{{ durationHours }}h</span>
          </div>
          <div class="flex justify-between">
            <span>Created</span>
            <span class="font-mono">{{ new Date(result.created_at).toLocaleString() }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-else class="flex flex-col items-center justify-center h-96 text-gray-500">
      <div class="animate-spin rounded-full h-16 w-16 border-t-2 border-[#3C83F8]"></div>
      <p class="mt-4 text-lg">Loading {{ currentScenario }}…</p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
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
  Filler
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const currentScenario = ref('scenario1')
const result = ref(null)
const nominalPowerMw = 100

// Load JSON
const loadScenario = async (name) => {
  try {
    const res = await fetch(`/data_test/${name}.json`)
    result.value = await res.json()
  } catch (e) {
    console.error('Erreur:', e)
  }
}

watch(currentScenario, loadScenario, { immediate: true })

// Durée
const durationHours = computed(() => currentScenario.value === 'scenario1' ? 1 : 24)

// KPIs
const utilisation = computed(() => {
  if (!result.value) return 0
  return Math.round(result.value.total_supply_mwh / (nominalPowerMw * durationHours.value) * 100)
})

const totalDemand = computed(() => result.value?.total_demand_mwh ?? 0)
const balanceLabel = computed(() => result.value?.balance_mwh?.toFixed(3) ?? '0.000')

// Graphique (exactement comme screenshot)
const chartData = computed(() => {
  const generators = result.value?.result_json?.generators_t?.['Nuclear Plant US03']?.p
  if (!generators) return { labels: [], datasets: [] }

  return {
    labels: Array.from({ length: generators.length }, (_, i) => `H${i + 1}`),
    datasets: [{
      label: 'Nuclear Plant',
      data: generators,
      borderColor: '#3C83F8',
      backgroundColor: 'rgba(60, 131, 248, 0.15)',
      fill: true,
      tension: 0.4,
      pointRadius: 3,
      pointHoverRadius: 6
    }]
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: { color: '#E2E8F0', font: { size: 14 }, padding: 20 }
    }
  },
  scales: {
    x: {
      ticks: { color: '#94A3B8', font: { size: 11 } },
      grid: { color: '#1E293B' }
    },
    y: {
      beginAtZero: true,
      ticks: { color: '#94A3B8', font: { size: 11 } },
      grid: { color: '#1E293B' },
      title: { display: true, text: 'Power (kW)', color: '#94A3B8', font: { size: 13 } }
    }
  }
}

// Formatters
const formatMwh = (value) => value.toFixed(1) + ' kWh'
</script>

<style scoped>
canvas { height: 400px !important; }
</style>
