<template>
  <div class="flex flex-col gap-6">
    <!-- Header with close button -->
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-bold text-gray-900 dark:text-white">
        Scenario Comparison
      </h2>
      <UButton
        icon="i-heroicons-x-mark"
        size="sm"
        color="neutral"
        variant="ghost"
        @click="$emit('close')"
      />
    </div>

    <!-- Scenario names -->
    <div class="grid grid-cols-2 gap-4">
      <div class="rounded-xl border border-blue-800/40 bg-blue-950/20 p-4 text-center">
        <span class="text-xs text-gray-600 dark:text-gray-400 uppercase tracking-wider">Scenario A</span>
        <p class="text-sm font-semibold text-blue-400 mt-1 truncate">
          {{ scenarioA.name ?? scenarioA.id.slice(0, 8) }}
        </p>
      </div>
      <div class="rounded-xl border border-purple-800/40 bg-purple-950/20 p-4 text-center">
        <span class="text-xs text-gray-600 dark:text-gray-400 uppercase tracking-wider">Scenario B</span>
        <p class="text-sm font-semibold text-purple-400 mt-1 truncate">
          {{ scenarioB.name ?? scenarioB.id.slice(0, 8) }}
        </p>
      </div>
    </div>

    <!-- KPI delta table -->
    <div class="bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-gray-200 dark:border-slate-800">
            <th class="text-left px-5 py-3 text-xs font-semibold uppercase tracking-wider text-gray-600 dark:text-gray-400">
              KPI
            </th>
            <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-blue-400">
              A
            </th>
            <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-purple-400">
              B
            </th>
            <th class="text-right px-5 py-3 text-xs font-semibold uppercase tracking-wider text-gray-600 dark:text-gray-400">
              Delta
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in kpiRows"
            :key="row.label"
            class="border-b border-gray-100 dark:border-slate-800/50 last:border-b-0"
          >
            <td class="px-5 py-3 text-gray-700 dark:text-gray-300 font-medium">
              {{ row.label }}
              <span class="text-gray-600 text-xs ml-1">{{ row.unit }}</span>
            </td>
            <td class="text-right px-5 py-3 font-mono text-blue-400">
              {{ fmtVal(row.a) }}
            </td>
            <td class="text-right px-5 py-3 font-mono text-purple-400">
              {{ fmtVal(row.b) }}
            </td>
            <td
              class="text-right px-5 py-3 font-mono font-semibold"
              :class="deltaColor(row.delta, row.lowerIsBetter)"
            >
              {{ fmtDelta(row.delta) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Capacity factor comparison chart -->
    <div
      v-if="hasCapacityFactors"
      class="bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 p-5"
    >
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider">
          Capacity Factors Comparison
        </h2>
        <span class="text-xs text-gray-500">%</span>
      </div>
      <BaseChart
        :option="cfChartOption"
        title="Capacity Factors Comparison"
      />
    </div>

    <!-- Empty state if no capacity factors -->
    <div
      v-else
      class="bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 p-8 text-center text-gray-500 text-sm"
    >
      No capacity factor data available for comparison.
    </div>
  </div>
</template>

<script setup lang="ts">
import type { SimulationResult } from '~/composables/api'

const props = defineProps<{
  scenarioA: SimulationResult
  scenarioB: SimulationResult
}>()

defineEmits<{ close: [] }>()

const { barOption } = useEChartsTheme()

// ── Helpers ────────────────────────────────────────────────────────────────────

function fmtVal(v: number | null): string {
  if (v == null) return '--'
  if (Math.abs(v) >= 1000) return `${(v / 1000).toFixed(1)}k`
  return v.toFixed(1)
}

function fmtDelta(v: number | null): string {
  if (v == null) return '--'
  const sign = v > 0 ? '+' : ''
  if (Math.abs(v) >= 1000) return `${sign}${(v / 1000).toFixed(1)}k`
  return `${sign}${v.toFixed(1)}`
}

function deltaColor(delta: number | null, lowerIsBetter: boolean): string {
  if (delta == null || Math.abs(delta) < 0.01) return 'text-gray-500'
  const isGood = lowerIsBetter ? delta < 0 : delta > 0
  return isGood ? 'text-emerald-400' : 'text-red-400'
}

// ── KPI rows ───────────────────────────────────────────────────────────────────

interface KpiRow {
  label: string
  unit: string
  a: number | null
  b: number | null
  delta: number | null
  lowerIsBetter: boolean
}

const kpiRows = computed<KpiRow[]>(() => {
  const a = props.scenarioA
  const b = props.scenarioB
  return [
    {
      label: 'Total Supply',
      unit: 'MWh',
      a: a.total_supply_mwh,
      b: b.total_supply_mwh,
      delta: computeDelta(a.total_supply_mwh, b.total_supply_mwh),
      lowerIsBetter: false
    },
    {
      label: 'Total Demand',
      unit: 'MWh',
      a: a.total_demand_mwh,
      b: b.total_demand_mwh,
      delta: computeDelta(a.total_demand_mwh, b.total_demand_mwh),
      lowerIsBetter: true
    },
    {
      label: 'Balance',
      unit: 'MWh',
      a: a.balance_mwh,
      b: b.balance_mwh,
      delta: computeDelta(a.balance_mwh, b.balance_mwh),
      lowerIsBetter: false
    },
    {
      label: 'Objective Value',
      unit: 'EUR',
      a: a.objective_value,
      b: b.objective_value,
      delta: computeDelta(a.objective_value, b.objective_value),
      lowerIsBetter: true
    }
  ]
})

function computeDelta(a: number | null | undefined, b: number | null | undefined): number | null {
  if (a == null || b == null) return null
  return b - a
}

// ── Capacity factor chart ──────────────────────────────────────────────────────

const hasCapacityFactors = computed(() => {
  const cfA = props.scenarioA.result_json?.capacity_factors ?? {}
  const cfB = props.scenarioB.result_json?.capacity_factors ?? {}
  return Object.keys(cfA).length > 0 || Object.keys(cfB).length > 0
})

const cfChartOption = computed(() => {
  const cfA = props.scenarioA.result_json?.capacity_factors ?? {}
  const cfB = props.scenarioB.result_json?.capacity_factors ?? {}

  const allKeys = [...new Set([...Object.keys(cfA), ...Object.keys(cfB)])]

  return barOption({
    labels: allKeys,
    series: [
      {
        name: 'Scenario A',
        data: allKeys.map(k => +((cfA[k] ?? 0) * 100).toFixed(1)),
        color: '#3B82F6'
      },
      {
        name: 'Scenario B',
        data: allKeys.map(k => +((cfB[k] ?? 0) * 100).toFixed(1)),
        color: '#A855F7'
      }
    ],
    yTitle: '%',
    yMax: 100,
    tooltipSuffix: ' %',
    showLegend: true
  })
})
</script>
