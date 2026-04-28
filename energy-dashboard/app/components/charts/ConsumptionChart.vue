<template>
  <div class="bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 p-5">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider">
        {{ $t('charts.consumptionByLoad') }}
      </h2>
      <span class="text-xs text-gray-500">MW / hour</span>
    </div>
    <BaseChart
      :option="chartOption"
      height="h-72"
      :title="$t('charts.consumptionByLoad')"
    />

    <!-- Residential load profile info -->
    <div
      v-if="hasHouseLoad"
      class="mt-3 flex items-start gap-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 px-3 py-2"
    >
      <UIcon
        name="i-heroicons-home"
        class="w-4 h-4 text-emerald-400 shrink-0 mt-0.5"
      />
      <p class="text-[11px] text-emerald-300 leading-relaxed">
        <strong>Residential profile</strong> — CBS Netherlands 2023 (10 household types, 500 homes).
        Evening peak at 18h (cooking + appliances), morning peak at 08h–09h, night trough at 03h–04h.
      </p>
    </div>

    <!-- EV charging pattern info -->
    <div
      v-if="hasEvLoad"
      class="mt-3 flex items-start gap-2 rounded-lg bg-blue-500/10 border border-blue-500/20 px-3 py-2"
    >
      <UIcon
        name="i-heroicons-bolt"
        class="w-4 h-4 text-blue-400 shrink-0 mt-0.5"
      />
      <p class="text-[11px] text-blue-300 leading-relaxed">
        <strong>EV charging profile</strong> — based on real data (6 charging channels, 16 BEVs).
        Peak at 18h–19h (evening return), zero at 07h &amp; 17h (commute). Daytime charge via workplace and fast-charging stations.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'

const props = defineProps<{ result: SimulationResult, startDate?: string | null }>()
const { lineOption } = useEChartsTheme()
const { buildLabels, axisLabelFormatter, tooltipLabelFormatter } = useTimeLabels(() => props.startDate)

const loadsT = computed(() => props.result.result_json?.loads_t ?? {})
const timeLabels = computed(() => buildLabels(Object.values(loadsT.value)[0]?.p?.length ?? 0))

const hasHouseLoad = computed(() =>
  Object.keys(loadsT.value).some((name) => {
    const n = name.toLowerCase()
    return n.includes('house') || n.includes('residential') || n.includes('home')
  })
)

const hasEvLoad = computed(() =>
  Object.keys(loadsT.value).some((name) => {
    const n = name.toLowerCase()
    return n.includes('ev') || n.includes('vehicle') || n.includes('electric')
  })
)

const chartOption = computed(() =>
  lineOption({
    labels: timeLabels.value,
    series: Object.entries(loadsT.value).map(([name, data], i) => ({
      name,
      data: (data as { p: number[] }).p,
      color: PALETTE[(i + 4) % PALETTE.length] as string
    })),
    yTitle: 'MW',
    axisLabelFormatter,
    tooltipLabelFormatter
  })
)
</script>
