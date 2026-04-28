<template>
  <div class="flex flex-col items-center justify-center flex-1 min-h-96 py-10 px-4">
    <!-- Skip link -->
    <div class="w-full max-w-2xl flex justify-end mb-2">
      <button
        class="text-xs text-gray-500 hover:text-gray-300 transition-colors"
        @click="$emit('complete')"
      >
        Skip wizard
      </button>
    </div>

    <!-- Step indicator -->
    <div class="flex items-center gap-2 mb-8">
      <template
        v-for="(s, i) in steps"
        :key="i"
      >
        <button
          class="w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold transition-colors"
          :class="
            i === step
              ? 'bg-blue-600 text-white'
              : i < step
                ? 'bg-blue-900 text-blue-300'
                : 'bg-slate-800 text-gray-500'
          "
          @click="i < step ? step = i : undefined"
        >
          {{ i + 1 }}
        </button>
        <div
          v-if="i < steps.length - 1"
          class="w-10 h-0.5"
          :class="i < step ? 'bg-blue-700' : 'bg-slate-700'"
        />
      </template>
    </div>

    <!-- Step card -->
    <div class="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
      <!-- Step 1: Demand -->
      <div v-if="step === 0">
        <h2 class="text-lg font-semibold text-white mb-1">
          How much electricity does your grid need?
        </h2>
        <p class="text-sm text-gray-400 mb-5">
          Start by selecting the consumers. Each house draws ~10 MW with a realistic 24h profile
          peaking at 6-7 PM (evening cooking, heating). Electric vehicles charge mainly at night.
        </p>

        <div
          v-if="referential.availableDemands.length === 0"
          class="text-sm text-gray-500 italic"
        >
          No demand assets available. Add some from the sidebar first.
        </div>
        <div
          v-else
          class="flex flex-col gap-3"
        >
          <label
            v-for="d in referential.availableDemands"
            :key="d.id"
            class="flex items-center gap-3 p-3 rounded-lg border transition-colors cursor-pointer"
            :class="
              selectedDemandIds.has(d.id)
                ? 'border-blue-600 bg-blue-950/40'
                : 'border-slate-700 bg-slate-800/50 hover:border-slate-600'
            "
          >
            <input
              type="checkbox"
              :checked="selectedDemandIds.has(d.id)"
              class="accent-blue-500 w-4 h-4"
              @change="toggleDemand(d.id)"
            >
            <span class="text-lg">{{ demandIcon(d.type) }}</span>
            <div class="flex-1 min-w-0">
              <span class="text-sm text-white font-medium">{{ d.name }}</span>
              <span class="text-xs text-gray-500 ml-2">{{ d.load_mw }} MW &middot; {{ d.type.replace('_', ' ') }}</span>
            </div>
          </label>
        </div>
      </div>

      <!-- Step 2: Supply -->
      <div v-if="step === 1">
        <h2 class="text-lg font-semibold text-white mb-1">
          How will you generate electricity?
        </h2>
        <p class="text-sm text-gray-400 mb-5">
          Solar panels produce only during daytime (weather-dependent, KNMI data). Wind turbines
          depend on wind speed. Nuclear provides stable baseload. Batteries store surplus for later.
          The optimizer will dispatch them by cost: free renewables first, then nuclear, then grid
          import as last resort.
        </p>

        <div
          v-if="referential.availableSupplies.length === 0"
          class="text-sm text-gray-500 italic"
        >
          No supply assets available. Add some from the sidebar first.
        </div>
        <div
          v-else
          class="flex flex-col gap-3"
        >
          <label
            v-for="s in referential.availableSupplies"
            :key="s.id"
            class="flex items-center gap-3 p-3 rounded-lg border transition-colors cursor-pointer"
            :class="
              selectedSupplyIds.has(s.id)
                ? 'border-blue-600 bg-blue-950/40'
                : 'border-slate-700 bg-slate-800/50 hover:border-slate-600'
            "
          >
            <input
              type="checkbox"
              :checked="selectedSupplyIds.has(s.id)"
              class="accent-blue-500 w-4 h-4"
              @change="toggleSupply(s.id)"
            >
            <span
              class="text-lg"
              :class="supplyColor(s.type)"
            >{{ supplyIcon(s.type) }}</span>
            <div class="flex-1 min-w-0">
              <span class="text-sm text-white font-medium">{{ s.name }}</span>
              <span class="text-xs text-gray-500 ml-2">{{ s.capacity_mw }} MW &middot; {{ s.type.replace(/_/g, ' ') }}</span>
            </div>
          </label>
        </div>
      </div>

      <!-- Step 3: Parameters -->
      <div v-if="step === 2">
        <h2 class="text-lg font-semibold text-white mb-1">
          How long should we simulate?
        </h2>
        <p class="text-sm text-gray-400 mb-5">
          Duration in hours (24h = 1 day, 168h = 1 week, 8760h = 1 year). Longer simulations
          capture seasonal patterns but take more time. The optimizer finds the cheapest way to meet
          demand hour by hour.
        </p>

        <!-- Duration presets -->
        <div class="mb-5">
          <label class="text-xs text-gray-500 uppercase tracking-wide mb-2 block">Duration</label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="preset in durationPresets"
              :key="preset.value"
              class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
              :class="
                sim.snapshotHours === preset.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-800 text-gray-400 hover:bg-slate-700 hover:text-gray-200'
              "
              @click="sim.snapshotHours = preset.value"
            >
              {{ preset.label }}
            </button>
          </div>
          <div class="mt-3 flex items-center gap-2">
            <label class="text-xs text-gray-500">Custom hours:</label>
            <input
              v-model.number="sim.snapshotHours"
              type="number"
              min="1"
              class="w-24 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sm text-white focus:border-blue-500 focus:outline-none"
            >
          </div>
        </div>

        <!-- Optimization objective -->
        <div>
          <label class="text-xs text-gray-500 uppercase tracking-wide mb-2 block">
            Optimization objective
          </label>
          <div class="flex flex-col gap-2">
            <label
              v-for="obj in objectives"
              :key="obj.value"
              class="flex items-start gap-3 p-3 rounded-lg border transition-colors cursor-pointer"
              :class="
                sim.optimizationObjective === obj.value
                  ? 'border-blue-600 bg-blue-950/40'
                  : 'border-slate-700 bg-slate-800/50 hover:border-slate-600'
              "
            >
              <input
                type="radio"
                :value="obj.value"
                :checked="sim.optimizationObjective === obj.value"
                class="accent-blue-500 mt-0.5"
                @change="sim.optimizationObjective = obj.value"
              >
              <div>
                <span class="text-sm text-white font-medium">{{ obj.label }}</span>
                <p class="text-xs text-gray-500 mt-0.5">{{ obj.description }}</p>
              </div>
            </label>
          </div>
        </div>
      </div>

      <!-- Step 4: Run -->
      <div v-if="step === 3">
        <h2 class="text-lg font-semibold text-white mb-1">
          Ready to simulate!
        </h2>
        <p class="text-sm text-gray-400 mb-5">
          PyPSA will run a Linear Optimal Power Flow (LOPF), finding the cheapest dispatch that
          meets demand at every hour while respecting physical constraints.
        </p>

        <!-- Summary -->
        <div class="bg-slate-800 rounded-lg p-4 mb-5 space-y-3">
          <div>
            <span class="text-xs text-gray-500 uppercase tracking-wide">Demand</span>
            <div class="flex flex-wrap gap-1 mt-1">
              <span
                v-for="d in selectedDemandsList"
                :key="d.id"
                class="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-700 text-xs text-gray-300"
              >
                {{ demandIcon(d.type) }} {{ d.name }}
              </span>
              <span
                v-if="selectedDemandsList.length === 0"
                class="text-xs text-gray-600 italic"
              >
                None selected
              </span>
            </div>
          </div>
          <div>
            <span class="text-xs text-gray-500 uppercase tracking-wide">Supply</span>
            <div class="flex flex-wrap gap-1 mt-1">
              <span
                v-for="s in selectedSuppliesList"
                :key="s.id"
                class="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-700 text-xs text-gray-300"
              >
                {{ supplyIcon(s.type) }} {{ s.name }}
              </span>
              <span
                v-if="selectedSuppliesList.length === 0"
                class="text-xs text-gray-600 italic"
              >
                None selected
              </span>
            </div>
          </div>
          <div class="flex gap-6">
            <div>
              <span class="text-xs text-gray-500 uppercase tracking-wide">Duration</span>
              <p class="text-sm text-white">
                {{ sim.snapshotHours }}h
              </p>
            </div>
            <div>
              <span class="text-xs text-gray-500 uppercase tracking-wide">Objective</span>
              <p class="text-sm text-white">
                {{ objectives.find(o => o.value === sim.optimizationObjective)?.label }}
              </p>
            </div>
          </div>
        </div>

        <!-- Run button -->
        <button
          class="w-full py-3 rounded-lg font-semibold text-white text-base transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          :class="canRun ? 'bg-blue-600 hover:bg-blue-500' : 'bg-slate-700'"
          :disabled="!canRun || sim.isRunning"
          @click="handleRun"
        >
          <template v-if="sim.isRunning">
            Running...
          </template>
          <template v-else>
            Run Simulation
          </template>
        </button>
        <p
          v-if="!canRun"
          class="text-xs text-amber-500 mt-2 text-center"
        >
          Select at least one demand and one supply asset to run.
        </p>
        <p
          v-if="sim.error"
          class="text-xs text-red-400 mt-2 text-center"
        >
          {{ sim.error }}
        </p>
      </div>
    </div>

    <!-- Navigation buttons -->
    <div class="w-full max-w-2xl flex justify-between mt-4">
      <button
        v-if="step > 0"
        class="px-5 py-2 rounded-lg text-sm font-medium bg-slate-800 text-gray-400 hover:bg-slate-700 hover:text-white transition-colors"
        @click="step--"
      >
        Back
      </button>
      <div v-else />
      <button
        v-if="step < steps.length - 1"
        class="px-5 py-2 rounded-lg text-sm font-medium bg-blue-600 text-white hover:bg-blue-500 transition-colors"
        @click="step++"
      >
        Next
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useSimulationStore } from '~/stores/simulation'
import { useReferentialStore } from '~/stores/referential'

const emit = defineEmits<{
  complete: []
}>()

const sim = useSimulationStore()
const referential = useReferentialStore()

const step = ref(0)

const steps = ['Demand', 'Supply', 'Parameters', 'Run']

// --- Local selection tracking (synced to store) ---

const selectedDemandIds = ref(new Set<string>(sim.selectedDemandIds))
const selectedSupplyIds = ref(new Set<string>(sim.selectedSupplyIds))

function toggleDemand(id: string) {
  if (selectedDemandIds.value.has(id)) {
    selectedDemandIds.value.delete(id)
    sim.removeDemandFromSelection(id)
  } else {
    selectedDemandIds.value.add(id)
    sim.addDemandToSelection(id)
  }
  // Trigger reactivity
  selectedDemandIds.value = new Set(selectedDemandIds.value)
}

function toggleSupply(id: string) {
  if (selectedSupplyIds.value.has(id)) {
    selectedSupplyIds.value.delete(id)
    sim.removeSupplyFromSelection(id)
  } else {
    selectedSupplyIds.value.add(id)
    sim.addSupplyToSelection(id)
  }
  selectedSupplyIds.value = new Set(selectedSupplyIds.value)
}

// --- Computed lists for summary ---

const selectedDemandsList = computed(() =>
  referential.availableDemands.filter(d => selectedDemandIds.value.has(d.id))
)
const selectedSuppliesList = computed(() =>
  referential.availableSupplies.filter(s => selectedSupplyIds.value.has(s.id))
)

const canRun = computed(() =>
  selectedDemandIds.value.size > 0 && selectedSupplyIds.value.size > 0
)

// --- Duration presets ---

const durationPresets = [
  { label: '24h (1 day)', value: 24 },
  { label: '168h (1 week)', value: 168 },
  { label: '720h (1 month)', value: 720 },
  { label: '8760h (1 year)', value: 8760 }
]

// --- Objectives ---

const objectives = [
  {
    value: 'min_cost' as const,
    label: 'Minimize cost',
    description: 'Find the cheapest dispatch to meet demand. Prioritizes low marginal-cost sources (renewables, nuclear).'
  },
  {
    value: 'min_emissions' as const,
    label: 'Minimize emissions',
    description: 'Reduce CO2 by favoring zero-carbon sources, even if more expensive.'
  },
  {
    value: 'max_renewable' as const,
    label: 'Maximize renewables',
    description: 'Maximize the share of wind and solar in the energy mix.'
  }
]

// --- Icons and colors ---

function demandIcon(type: string): string {
  switch (type) {
    case 'house': return '\u{1F3E0}'
    case 'electric_vehicle': return '\u{1F697}'
    default: return '\u{26A1}'
  }
}

function supplyIcon(type: string): string {
  switch (type) {
    case 'solar_panel': return '\u{2600}\u{FE0F}'
    case 'wind_turbine': return '\u{1F32C}\u{FE0F}'
    case 'nuclear_plant': return '\u{2622}\u{FE0F}'
    default: return '\u{1F50B}'
  }
}

function supplyColor(type: string): string {
  switch (type) {
    case 'solar_panel': return 'text-yellow-400'
    case 'wind_turbine': return 'text-blue-400'
    case 'nuclear_plant': return 'text-purple-400'
    default: return 'text-green-400'
  }
}

// --- Run ---

async function handleRun() {
  try {
    await sim.runFullSimulation()
    emit('complete')
  } catch {
    // error is displayed via sim.error
  }
}
</script>
