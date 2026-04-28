<template>
  <Teleport to="body">
    <Transition name="tut">
      <div
        v-if="visible"
        class="fixed inset-0 z-[100] flex items-end justify-end p-6 pointer-events-none"
      >
        <!-- Dimmed backdrop (only on step 0) -->
        <Transition name="fade">
          <div
            v-if="step === 0"
            class="absolute inset-0 bg-black/60 pointer-events-auto"
            @click="next"
          />
        </Transition>

        <!-- Tutorial card -->
        <div class="relative pointer-events-auto w-[380px] bg-white dark:bg-slate-950 border border-gray-300 dark:border-slate-700 rounded-2xl shadow-2xl overflow-hidden">
          <!-- Progress bar -->
          <div class="h-0.5 bg-gray-200 dark:bg-slate-800">
            <div
              class="h-full bg-blue-500 transition-all duration-500"
              :style="{ width: `${((step + 1) / steps.length) * 100}%` }"
            />
          </div>

          <!-- Step indicator -->
          <div class="flex items-center gap-1.5 px-5 pt-4 pb-0">
            <button
              v-for="(_, i) in steps"
              :key="i"
              class="h-1.5 rounded-full transition-all duration-300"
              :class="i === step ? 'w-5 bg-blue-500' : i < step ? 'w-1.5 bg-blue-800' : 'w-1.5 bg-gray-200 dark:bg-slate-800'"
              @click="step = i"
            />
            <span class="ml-auto text-[11px] text-gray-600 font-mono">{{ step + 1 }}/{{ steps.length }}</span>
          </div>

          <!-- Content -->
          <div class="px-5 pt-3 pb-5">
            <Transition
              :name="direction === 'next' ? 'slide-left' : 'slide-right'"
              mode="out-in"
            >
              <div :key="step">
                <!-- Icon -->
                <div
                  class="w-10 h-10 rounded-xl flex items-center justify-center mb-3"
                  :class="current.iconBg"
                >
                  <UIcon
                    :name="current.icon"
                    class="w-5 h-5"
                    :class="current.iconColor"
                  />
                </div>

                <!-- Title -->
                <h3 class="text-base font-bold text-gray-900 dark:text-white mb-2 leading-snug">
                  {{ current.title }}
                </h3>

                <!-- Description -->
                <p class="text-sm text-gray-600 dark:text-gray-400 leading-relaxed mb-3">
                  {{ current.description }}
                </p>

                <!-- Visual detail block -->
                <div
                  v-if="current.detail"
                  class="bg-gray-50 dark:bg-slate-950 rounded-xl border border-gray-200 dark:border-slate-800 p-3 space-y-2"
                >
                  <div
                    v-for="row in current.detail"
                    :key="row.label"
                    class="flex items-start gap-2.5"
                  >
                    <div
                      class="w-5 h-5 rounded flex items-center justify-center shrink-0 mt-0.5"
                      :class="row.bg"
                    >
                      <UIcon
                        :name="row.icon"
                        class="w-3 h-3"
                        :class="row.color"
                      />
                    </div>
                    <div class="min-w-0">
                      <p class="text-xs font-semibold text-gray-900 dark:text-white leading-tight">
                        {{ row.label }}
                      </p>
                      <p class="text-[11px] text-gray-500 leading-tight mt-0.5">
                        {{ row.desc }}
                      </p>
                    </div>
                  </div>
                </div>

                <!-- Highlight hint (where to look) -->
                <div
                  v-if="current.hint"
                  class="mt-3 flex items-center gap-2 text-[11px] text-gray-500"
                >
                  <UIcon
                    name="i-heroicons-cursor-arrow-rays"
                    class="w-3.5 h-3.5 text-blue-500 shrink-0"
                  />
                  <span>{{ current.hint }}</span>
                </div>
              </div>
            </Transition>
          </div>

          <!-- Footer actions -->
          <div class="px-5 pb-5 flex items-center gap-2">
            <UButton
              v-if="step > 0"
              label="Back"
              color="neutral"
              variant="ghost"
              size="sm"
              @click="prev"
            />
            <div class="flex-1" />
            <UButton
              v-if="step < steps.length - 1"
              label="Next"
              color="primary"
              size="sm"
              trailing-icon="i-heroicons-arrow-right"
              @click="next"
            />
            <UButton
              v-else
              label="Start exploring"
              color="primary"
              size="sm"
              trailing-icon="i-heroicons-rocket-launch"
              @click="finish"
            />
            <UButton
              v-if="step < steps.length - 1"
              label="Skip"
              color="neutral"
              variant="ghost"
              size="sm"
              @click="finish"
            />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
const STORAGE_KEY = 'ens_tutorial_done'

const visible = ref(false)
const step = ref(0)
const direction = ref<'next' | 'prev'>('next')

onMounted(() => {
  if (!localStorage.getItem(STORAGE_KEY)) {
    visible.value = true
  }
})

function next() {
  direction.value = 'next'
  step.value = Math.min(step.value + 1, steps.length - 1)
}
function prev() {
  direction.value = 'prev'
  step.value = Math.max(step.value - 1, 0)
}
function finish() {
  localStorage.setItem(STORAGE_KEY, '1')
  visible.value = false
}

// Expose so parent can re-open
defineExpose({ open: () => {
  step.value = 0
  visible.value = true
} })

interface DetailRow {
  icon: string
  label: string
  desc: string
  bg: string
  color: string
}
interface Step {
  icon: string
  iconBg: string
  iconColor: string
  title: string
  description: string
  detail?: DetailRow[]
  hint?: string
}

const steps: Step[] = [
  {
    icon: 'i-heroicons-bolt',
    iconBg: 'bg-blue-950',
    iconColor: 'text-blue-400',
    title: 'Welcome to the Energy Network Simulator',
    description: 'This platform lets you model a local electricity grid, run an optimal power flow simulation, and understand how production, storage, and consumption interact.',
    detail: [
      { icon: 'i-heroicons-bolt', label: 'You configure assets', desc: 'Generators, batteries, loads, and network components with real parameters (MW, efficiency…)', bg: 'bg-amber-950', color: 'text-amber-400' },
      { icon: 'i-heroicons-cpu-chip', label: 'PyPSA optimises the grid', desc: 'A Linear Optimal Power Flow (LOPF) finds the cheapest dispatch across all hours simultaneously', bg: 'bg-blue-950', color: 'text-blue-400' },
      { icon: 'i-heroicons-chart-bar', label: 'You read the results', desc: 'Production per generator, consumption per load, balance, and capacity factors', bg: 'bg-emerald-950', color: 'text-emerald-400' }
    ]
  },
  {
    icon: 'i-heroicons-squares-plus',
    iconBg: 'bg-amber-950',
    iconColor: 'text-amber-400',
    title: 'Step 1 — Select your assets',
    description: 'The sidebar on the left lets you build your grid. You need at least one supply and one demand to run a simulation.',
    detail: [
      { icon: 'i-heroicons-bolt', label: 'Supply — generators', desc: 'Wind turbines, solar panels, or nuclear plants. Each injects power into the grid.', bg: 'bg-amber-950', color: 'text-amber-400' },
      { icon: 'i-heroicons-home', label: 'Demand — loads', desc: 'Houses and EVs that consume power. Their hourly demand varies via a normalised profile.', bg: 'bg-emerald-950', color: 'text-emerald-400' },
      { icon: 'i-heroicons-share', label: 'Network — components', desc: 'Transformers and cables that link buses. Their MVA rating limits how much power can flow.', bg: 'bg-blue-950', color: 'text-blue-400' }
    ],
    hint: 'Look left → open the sidebar to browse and add assets from the catalogue.'
  },
  {
    icon: 'i-heroicons-adjustments-horizontal',
    iconBg: 'bg-violet-950',
    iconColor: 'text-violet-400',
    title: 'Step 2 — Configure parameters',
    description: 'Click any selected asset to adjust its parameters. These values determine how the generator or load behaves in the simulation.',
    detail: [
      { icon: 'i-heroicons-signal', label: 'Capacity (MW)', desc: 'The maximum instantaneous power this asset can deliver or consume. Think of it as the upper bound.', bg: 'bg-violet-950', color: 'text-violet-400' },
      { icon: 'i-heroicons-arrow-trending-up', label: 'Efficiency (0–1)', desc: 'For nuclear: fraction of thermal energy converted to electricity (e.g. 0.33). Wind/solar: already in the weather data.', bg: 'bg-violet-950', color: 'text-violet-400' },
      { icon: 'i-heroicons-cloud', label: 'Weather (wind & solar)', desc: 'Real KNMI data from Groningen Eelde (2025). Select a date range to use it — without one, generators run at full capacity.', bg: 'bg-sky-950', color: 'text-sky-400' }
    ],
    hint: 'Select an asset in the sidebar → a parameter panel appears below it.'
  },
  {
    icon: 'i-heroicons-clock',
    iconBg: 'bg-teal-950',
    iconColor: 'text-teal-400',
    title: 'Step 3 — Choose your time window',
    description: 'The LOPF optimises all hours simultaneously. A longer period gives more realistic averages and lets batteries shift energy across more hours.',
    detail: [
      { icon: 'i-heroicons-bolt', label: '1 hour', desc: 'A single snapshot — good for testing extreme peak scenarios.', bg: 'bg-teal-950', color: 'text-teal-400' },
      { icon: 'i-heroicons-sun', label: '24 hours', desc: 'One day — captures the solar day/night cycle and the daily demand curve.', bg: 'bg-teal-950', color: 'text-teal-400' },
      { icon: 'i-heroicons-calendar', label: '168 h / 8760 h', desc: 'One week or a full year — reveals multi-day wind lulls and seasonal patterns.', bg: 'bg-teal-950', color: 'text-teal-400' }
    ],
    hint: 'Look at the second header bar → Hours / Date range selector.'
  },
  {
    icon: 'i-heroicons-chart-bar-square',
    iconBg: 'bg-emerald-950',
    iconColor: 'text-emerald-400',
    title: 'Step 4 — Read the energy flow',
    description: 'After the simulation runs, the Results tab shows you exactly where electricity came from and where it went.',
    detail: [
      { icon: 'i-heroicons-bolt', label: 'Local production (MWh)', desc: 'Total energy injected by your generators. Broken down per asset in the Energy Flow panel.', bg: 'bg-emerald-950', color: 'text-emerald-400' },
      { icon: 'i-heroicons-arrows-right-left', label: 'Grid import / export', desc: 'The slack generator bridges any gap. Import = demand > local supply. Export = surplus production.', bg: 'bg-blue-950', color: 'text-blue-400' },
      { icon: 'i-heroicons-scale', label: 'Balance (MWh)', desc: 'Production minus consumption. Near zero = well-balanced grid. Large surplus or deficit = revisit your asset mix.', bg: 'bg-slate-800', color: 'text-slate-300' },
      { icon: 'i-heroicons-arrow-trending-up', label: 'Capacity factor (%)', desc: 'Actual output ÷ theoretical maximum. A wind farm at 30% CF produced 30% of its rated capacity on average.', bg: 'bg-violet-950', color: 'text-violet-400' }
    ],
    hint: 'Click "Save" to run the full simulation → check the Results and Energy Flow tabs.'
  }
]

const current = computed(() => steps[step.value]!)
</script>

<style scoped>
.tut-enter-active { transition: opacity 0.2s ease; }
.tut-leave-active { transition: opacity 0.15s ease; }
.tut-enter-from, .tut-leave-to { opacity: 0; }

.fade-enter-active { transition: opacity 0.3s; }
.fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.slide-left-enter-active,
.slide-left-leave-active,
.slide-right-enter-active,
.slide-right-leave-active { transition: all 0.2s ease; }

.slide-left-enter-from  { opacity: 0; transform: translateX(16px); }
.slide-left-leave-to    { opacity: 0; transform: translateX(-16px); }
.slide-right-enter-from { opacity: 0; transform: translateX(-16px); }
.slide-right-leave-to   { opacity: 0; transform: translateX(16px); }
</style>
