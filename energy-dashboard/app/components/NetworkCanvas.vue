<template>
  <div
    ref="canvasRef"
    class="relative w-full bg-gray-50 dark:bg-slate-950 rounded-2xl border border-gray-200 dark:border-slate-800 overflow-hidden"
    :style="{ height: `${canvasH}px` }"
  >
    <!-- Dot grid background -->
    <div
      class="absolute inset-0 pointer-events-none"
      style="background-image: radial-gradient(circle, rgba(148,163,184,0.06) 1px, transparent 1px); background-size: 28px 28px;"
    />

    <!-- SVG cable layer -->
    <NetworkCanvasCableLayer
      v-if="canvasW > 0"
      :lines="cableLines"
      :canvas-w="canvasW"
      :canvas-h="canvasH"
    />

    <!-- ── Supply cards ──────────────────────────────────────────────────── -->
    <div
      v-for="(supply, i) in supplies"
      :key="supply.id"
      class="absolute bg-white dark:bg-slate-950 border border-gray-200 dark:border-slate-800 rounded-xl flex items-center hover:border-gray-300 dark:hover:border-slate-700 transition-colors duration-200 cursor-default"
      :class="lv.cardPad"
      :style="supplyCardStyle(i)"
      @mouseenter="showTooltip('supply', supply, $event)"
      @mousemove="moveTooltip($event)"
      @mouseleave="hideTooltip"
    >
      <NetworkCanvasAssetIcon
        v-if="!isMicro"
        :type="supply.type"
        :size="lv.iconSize"
        class="shrink-0"
      />
      <div
        class="min-w-0 flex-1"
        :class="isMicro ? '' : lv.cardGap"
      >
        <p
          class="font-semibold text-gray-900 dark:text-white truncate leading-tight"
          :class="lv.cardTitle"
        >
          {{ supply.name }}
        </p>
        <p
          class="text-gray-500 leading-tight"
          :class="lv.cardSub"
        >
          {{ supply.capacity_mw }} MW
        </p>
        <p
          v-if="result && !isMicro"
          class="font-mono text-emerald-400 leading-tight"
          :class="lv.cardSub"
        >
          ⚡ {{ fmtPow(supplyAvg(supply)) }} MW avg
        </p>
        <p
          v-else-if="result && isMicro"
          class="font-mono text-emerald-400 leading-tight text-[9px]"
        >
          {{ fmtPow(supplyAvg(supply)) }} MW
        </p>
      </div>
    </div>

    <!-- ── Demand cards ──────────────────────────────────────────────────── -->
    <div
      v-for="(demand, i) in demands"
      :key="demand.id"
      class="absolute bg-white dark:bg-slate-950 border border-gray-200 dark:border-slate-800 rounded-xl flex items-center hover:border-gray-300 dark:hover:border-slate-700 transition-colors duration-200 cursor-default"
      :class="lv.cardPad"
      :style="demandCardStyle(i)"
      @mouseenter="showTooltip('demand', demand, $event)"
      @mousemove="moveTooltip($event)"
      @mouseleave="hideTooltip"
    >
      <NetworkCanvasAssetIcon
        v-if="!isMicro"
        :type="demand.type"
        :size="lv.iconSize"
        class="shrink-0"
      />
      <div
        class="min-w-0 flex-1"
        :class="isMicro ? '' : lv.cardGap"
      >
        <p
          class="font-semibold text-gray-900 dark:text-white truncate leading-tight"
          :class="lv.cardTitle"
        >
          {{ demand.name }}
        </p>
        <p
          class="text-gray-500 leading-tight"
          :class="lv.cardSub"
        >
          {{ demand.load_mw }} MW
        </p>
        <p
          v-if="result && !isMicro"
          class="font-mono text-red-400 leading-tight"
          :class="lv.cardSub"
        >
          🔌 {{ fmtPow(demandAvg(demand)) }} MW avg
        </p>
        <p
          v-else-if="result && isMicro"
          class="font-mono text-red-400 leading-tight text-[9px]"
        >
          {{ fmtPow(demandAvg(demand)) }} MW
        </p>
      </div>
    </div>

    <!-- ── Bus node (single bus – original) ─────────────────────────────── -->
    <div
      v-if="!isMultiBus"
      class="absolute flex flex-col items-center"
      :style="{ left: `${busX}px`, top: `${busY}px`, transform: 'translate(-50%, -50%)' }"
    >
      <!-- Glow ring -->
      <div
        class="absolute rounded-full blur-2xl opacity-20 pointer-events-none"
        :class="busGlowColor"
        :style="{ width: `${lv.busSize + 16}px`, height: `${lv.busSize + 16}px`, top: '-8px', left: '-8px' }"
      />
      <!-- Bus circle -->
      <div
        class="relative flex flex-col items-center justify-center rounded-full border-2 bg-white dark:bg-slate-950 cursor-default"
        :style="{ width: `${lv.busSize}px`, height: `${lv.busSize}px` }"
        :class="busBorderColor"
        @mouseenter="showTooltip('bus', null, $event)"
        @mousemove="moveTooltip($event)"
        @mouseleave="hideTooltip"
      >
        <svg
          :width="lv.busIconSize"
          :height="lv.busIconSize"
          viewBox="0 0 24 24"
          fill="none"
        >
          <path
            d="M13 2L4.5 13.5H11L10 22L19.5 10.5H13L13 2Z"
            :fill="busIconFill"
            stroke="none"
          />
        </svg>
        <span
          v-if="!isCompact"
          class="text-[9px] text-gray-500 font-mono leading-none mt-0.5"
        >380 kV</span>
      </div>
      <!-- Bus label -->
      <div
        class="mt-1.5 text-center"
        :style="{ maxWidth: `${lv.busSize + 40}px` }"
      >
        <p
          class="font-semibold text-gray-400 truncate"
          :class="lv.busLabel"
        >
          Main Bus
        </p>
        <p
          v-if="result"
          class="font-semibold mt-0.5"
          :class="[lv.busLabel, busStatusColor]"
        >
          {{ busStatusLabel }}
        </p>
        <p
          v-else
          class="text-gray-700 mt-0.5"
          :class="lv.busLabel"
        >
          No result
        </p>
      </div>
      <!-- Network component badges (full layout only) -->
      <div
        v-if="network.length && isFull"
        class="mt-3 flex flex-col gap-1.5 w-44"
      >
        <div
          v-for="n in network"
          :key="n.id"
          class="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-white dark:bg-slate-950 border border-gray-200 dark:border-slate-800 text-[11px] cursor-default hover:border-gray-300 dark:hover:border-slate-700 transition-colors"
          @mouseenter="showTooltip('network', n, $event)"
          @mousemove="moveTooltip($event)"
          @mouseleave="hideTooltip"
        >
          <NetworkCanvasAssetIcon
            :type="n.type"
            :size="18"
          />
          <span class="text-gray-600 dark:text-gray-400 truncate">{{ n.name }}</span>
          <span class="text-gray-600 font-mono ml-auto shrink-0">{{ n.capacity_mva }} MVA</span>
        </div>
      </div>
    </div>

    <!-- ── Bus nodes (multi-bus topology) ─────────────────────────────── -->
    <template v-else>
      <div
        v-for="(busName, idx) in buses"
        :key="busName"
        class="absolute flex flex-col items-center"
        :style="multiBusStyle(idx)"
      >
        <div
          class="relative flex flex-col items-center justify-center rounded-full border-2 bg-white dark:bg-slate-950 cursor-default"
          :style="{ width: `${multiBusSize}px`, height: `${multiBusSize}px` }"
          :class="busBorderColor"
          @mouseenter="showTooltip('bus', busName as any, $event)"
          @mousemove="moveTooltip($event)"
          @mouseleave="hideTooltip"
        >
          <svg
            :width="20"
            :height="20"
            viewBox="0 0 24 24"
            fill="none"
          >
            <path
              d="M13 2L4.5 13.5H11L10 22L19.5 10.5H13L13 2Z"
              :fill="busIconFill"
              stroke="none"
            />
          </svg>
        </div>
        <div
          class="mt-1 text-center"
          style="max-width: 120px;"
        >
          <p class="font-semibold text-gray-400 text-[10px] truncate">
            {{ formatBusName(busName) }}
          </p>
        </div>
      </div>
      <!-- Status label below last bus -->
      <div
        class="absolute text-center"
        :style="{ left: `${canvasW / 2}px`, top: `${demandBusY + multiBusSize / 2 + 20}px`, transform: 'translateX(-50%)' }"
      >
        <p
          v-if="result"
          class="font-semibold"
          :class="[lv.busLabel, busStatusColor]"
        >
          {{ busStatusLabel }}
        </p>
        <p
          v-else
          class="text-gray-700"
          :class="lv.busLabel"
        >
          No result
        </p>
      </div>
    </template>

    <!-- ── Storage cards (batteries) ────────────────────────────────────── -->
    <div
      v-for="(bat, i) in (storage ?? [])"
      :key="`bat-${bat.id}`"
      class="absolute bg-white dark:bg-slate-950 border border-green-200 dark:border-green-900/60 rounded-xl flex items-center hover:border-green-300 dark:hover:border-green-700/60 transition-colors duration-200 cursor-default"
      :class="lv.cardPad"
      :style="storageCardStyle(i)"
      @mouseenter="showTooltip('supply', bat, $event)"
      @mousemove="moveTooltip($event)"
      @mouseleave="hideTooltip"
    >
      <NetworkCanvasAssetIcon
        v-if="!isMicro"
        type="battery_storage"
        :size="lv.iconSize"
        class="shrink-0"
      />
      <div
        class="min-w-0 flex-1"
        :class="isMicro ? '' : lv.cardGap"
      >
        <p
          class="font-semibold text-gray-900 dark:text-white truncate leading-tight"
          :class="lv.cardTitle"
        >
          {{ bat.name }}
        </p>
        <p
          class="text-green-500 leading-tight"
          :class="lv.cardSub"
        >
          {{ bat.capacity_mw }} MW
        </p>
        <p
          v-if="result && storageAvg(bat)"
          class="font-mono text-green-400 leading-tight"
          :class="lv.cardSub"
        >
          🔋 {{ fmtPow(Math.abs(storageAvg(bat))) }} MW avg
        </p>
      </div>
    </div>

    <!-- ── Timestamp ──────────────────────────────────────────────────────── -->
    <div
      v-if="result && isFull"
      class="absolute top-3 right-4 text-xs font-mono text-gray-600 select-none"
    >
      {{ timestamp }}
    </div>

    <!-- ── Side / section labels ─────────────────────────────────────────── -->
    <template v-if="!isColumn">
      <div
        v-if="supplies.length"
        class="absolute top-3 left-4 text-[10px] font-semibold uppercase tracking-widest text-gray-700 select-none"
      >
        Supply
      </div>
      <div
        v-if="demands.length"
        class="absolute top-3 text-[10px] font-semibold uppercase tracking-widest text-gray-700 select-none"
        :style="{ right: `${lv.padX + 2}px` }"
      >
        Demand
      </div>
    </template>
    <template v-else>
      <div
        v-if="supplies.length"
        class="absolute text-[10px] font-semibold uppercase tracking-widest text-gray-700 select-none"
        :style="{ top: `${COL_PAD_Y - 14}px`, left: `${lv.padX}px` }"
      >
        Supply
      </div>
      <div
        v-if="demands.length"
        class="absolute text-[10px] font-semibold uppercase tracking-widest text-gray-700 select-none"
        :style="{ top: `${colDemandStart - 14}px`, left: `${lv.padX}px` }"
      >
        Demand
      </div>
    </template>

    <!-- ── Empty state ────────────────────────────────────────────────────── -->
    <div
      v-if="!supplies.length && !demands.length"
      class="absolute inset-0 flex items-center justify-center pointer-events-none"
    >
      <p class="text-gray-700 text-sm text-center px-6">
        Add supply and demand assets to visualize the network
      </p>
    </div>
  </div>

  <!-- ── Floating tooltip (teleported to body to escape overflow-hidden) ── -->
  <Teleport to="body">
    <Transition name="tip">
      <div
        v-if="tip.visible && tip.data"
        class="fixed z-[9999] pointer-events-none"
        :style="tipScreenStyle"
      >
        <div class="bg-white/95 dark:bg-slate-950/95 border border-gray-300 dark:border-slate-700 rounded-xl shadow-2xl p-3 w-56 backdrop-blur-sm">
          <!-- Header -->
          <div class="flex items-start justify-between gap-2 mb-2">
            <p class="text-gray-900 dark:text-white font-semibold text-xs leading-tight">
              {{ tip.data.name }}
            </p>
            <span
              class="shrink-0 text-[10px] px-1.5 py-0.5 rounded font-medium"
              :class="tipBadgeClass"
            >{{ tip.data.typeLabel }}</span>
          </div>

          <!-- Static params -->
          <div class="space-y-1 text-[11px]">
            <div
              v-for="row in tip.data.params"
              :key="row.label"
              class="flex justify-between items-start gap-2"
            >
              <span class="text-gray-500 leading-tight">{{ row.label }}</span>
              <span class="font-mono text-gray-700 dark:text-gray-300 text-right leading-tight shrink-0">{{ row.value }}</span>
            </div>
          </div>

          <!-- Simulation results (if available) -->
          <template v-if="tip.data.results && tip.data.results.length">
            <div class="border-t border-gray-200 dark:border-slate-800 mt-2 pt-2 space-y-1 text-[11px]">
              <p class="text-[10px] uppercase tracking-wider text-gray-600 mb-1">
                Simulation
              </p>
              <div
                v-for="row in tip.data.results"
                :key="row.label"
                class="flex justify-between items-start gap-2"
              >
                <span class="text-gray-500 leading-tight">{{ row.label }}</span>
                <span
                  class="font-mono leading-tight shrink-0"
                  :class="row.color ?? 'text-white'"
                >{{ row.value }}</span>
              </div>
            </div>
          </template>

          <!-- Explanation -->
          <p
            v-if="tip.data.hint"
            class="text-[10px] text-gray-600 mt-2 leading-relaxed border-t border-gray-200 dark:border-slate-800 pt-2"
          >
            {{ tip.data.hint }}
          </p>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import type { Supply, Demand, NetworkComponent, SimulationResult } from '~/composables/api'
import NetworkCanvasCableLayer from '~/components/network-canvas/CableLayer.vue'
import NetworkCanvasAssetIcon from '~/components/network-canvas/AssetIcon.vue'
import type { CableLine } from '~/components/network-canvas/CableLayer.vue'

const props = defineProps<{
  supplies: Supply[]
  storage?: Supply[]
  demands: Demand[]
  network: NetworkComponent[]
  result: SimulationResult | null
  visible?: boolean
}>()

// ── Canvas measure ────────────────────────────────────────────────────────────
const canvasRef = ref<HTMLElement | null>(null)
const canvasW = ref(0)

// ── Responsive flags ──────────────────────────────────────────────────────────
const isColumn = computed(() => canvasW.value > 0 && canvasW.value < 500)
const isMicro = computed(() => canvasW.value > 0 && canvasW.value < 400)
const isCompact = computed(() => canvasW.value > 0 && canvasW.value < 650)
const isFull = computed(() => canvasW.value >= 900)

// ── Layout values per breakpoint ──────────────────────────────────────────────
const lv = computed(() => {
  const w = canvasW.value
  if (w < 500) return {
    padX: w < 400 ? 6 : 10,
    cardW: 0, cardH: w < 400 ? 52 : 60, iconSize: w < 400 ? 0 : 28,
    busSize: w < 400 ? 52 : 64, busIconSize: w < 400 ? 18 : 22, gap: 8,
    cardPad: w < 400 ? 'p-1.5 gap-1' : 'p-2 gap-1.5', cardGap: w < 400 ? '' : 'ml-1.5',
    cardTitle: w < 400 ? 'text-[9px]' : 'text-[10px]', cardSub: w < 400 ? 'text-[9px]' : 'text-[10px]',
    busLabel: w < 400 ? 'text-[9px]' : 'text-[10px]'
  }
  if (w < 600) return {
    padX: 10, cardW: 130, cardH: 60, iconSize: 28, busSize: 60, busIconSize: 20, gap: 10,
    cardPad: 'p-2 gap-1.5', cardGap: 'ml-1.5', cardTitle: 'text-[10px]', cardSub: 'text-[10px]',
    busLabel: 'text-[10px]'
  }
  if (w < 800) return {
    padX: 16, cardW: 158, cardH: 68, iconSize: 36, busSize: 72, busIconSize: 24, gap: 12,
    cardPad: 'p-2 gap-2', cardGap: 'ml-2', cardTitle: 'text-[11px]', cardSub: 'text-[10px]',
    busLabel: 'text-[10px]'
  }
  if (w < 1100) return {
    padX: 22, cardW: 182, cardH: 76, iconSize: 44, busSize: 84, busIconSize: 30, gap: 14,
    cardPad: 'p-2.5 gap-2.5', cardGap: 'ml-2', cardTitle: 'text-xs', cardSub: 'text-[11px]',
    busLabel: 'text-[11px]'
  }
  return {
    padX: 28, cardW: 210, cardH: 82, iconSize: 52, busSize: 96, busIconSize: 36, gap: 14,
    cardPad: 'p-3 gap-3', cardGap: 'ml-1', cardTitle: 'text-xs', cardSub: 'text-[11px]',
    busLabel: 'text-xs'
  }
})

// ── Column-mode constants & derived heights ───────────────────────────────────
const COL_PAD_Y = 28
const COL_GAP = 20

const colCardW = computed(() => canvasW.value - 2 * lv.value.padX)
const colSupplyBlockH = computed(() => {
  const { cardH, gap } = lv.value
  const n = props.supplies.length
  return n ? n * cardH + (n - 1) * gap : 0
})
const colBusBlockH = computed(() => lv.value.busSize + 28)
const colDemandBlockH = computed(() => {
  const { cardH, gap } = lv.value
  const n = props.demands.length
  return n ? n * cardH + (n - 1) * gap : 0
})
const colBusStart = computed(() =>
  COL_PAD_Y + (props.supplies.length ? colSupplyBlockH.value + COL_GAP : 0)
)
const colDemandStart = computed(() =>
  colBusStart.value + colBusBlockH.value + COL_GAP
)

// ── Canvas height ─────────────────────────────────────────────────────────────
const canvasH = computed(() => {
  if (isColumn.value) {
    return COL_PAD_Y
      + (props.supplies.length ? colSupplyBlockH.value + COL_GAP : 0)
      + colBusBlockH.value
      + (props.demands.length ? COL_GAP + colDemandBlockH.value : 0)
      + COL_PAD_Y
  }
  const { cardH, gap } = lv.value
  const maxCards = Math.max(props.supplies.length, props.demands.length, 1)
  return Math.max(
    isMicro.value ? 260 : isCompact.value ? 320 : 460,
    maxCards * cardH + (maxCards - 1) * gap + 72
  )
})

// ── Bus position ──────────────────────────────────────────────────────────────
const busX = computed(() => canvasW.value / 2)
const busY = computed(() => {
  if (isColumn.value) return colBusStart.value + lv.value.busSize / 2
  return canvasH.value / 2
})
const busR = computed(() => lv.value.busSize / 2)

// ── Bus style (result-dependent) ──────────────────────────────────────────────
const busOk = computed(() => props.result?.status === 'converged' || props.result?.status === 'optimized' || props.result?.status === 'optimal')
const busGlowColor = computed(() => !props.result ? 'bg-gray-600' : busOk.value ? 'bg-emerald-500' : 'bg-red-500')
const busBorderColor = computed(() => !props.result ? 'border-slate-700' : busOk.value ? 'border-emerald-600/60' : 'border-red-600/60')
const busIconFill = computed(() => !props.result ? '#475569' : busOk.value ? '#34d399' : '#f87171')
const busStatusColor = computed(() => !props.result ? 'text-gray-600' : busOk.value ? 'text-emerald-400' : 'text-red-400')
const busStatusLabel = computed(() => {
  if (!props.result) return ''
  if (props.result.status === 'optimized') return 'Optimised'
  if (props.result.status === 'converged') return 'Converged'
  if (props.result.status === 'non_converged') return 'Non-conv.'
  return 'Error'
})

// ── Multi-bus detection ──────────────────────────────────────────────────────
const buses = computed(() => {
  const r = props.result?.result_json
  if (!r?.buses_t || Object.keys(r.buses_t).length <= 1) return null
  return Object.keys(r.buses_t)
})
const isMultiBus = computed(() => buses.value !== null && buses.value.length > 1)

const multiBusSize = computed(() => Math.max(48, lv.value.busSize - 16))

function formatBusName(name: string): string {
  const m = name.match(/bus_([\d.]+)kV/)
  if (!m) return name
  const afterKv = name.split('kV_')[1]
  const suffix = name.includes('kV_') && afterKv
    ? ` (${afterKv.replace(/_/g, ' ').replace(/ - /g, '-')})`
    : ''
  return `${m[1]} kV${suffix}`
}

function multiBusStyle(idx: number) {
  const total = buses.value?.length ?? 1
  const spacing = Math.min(80, (canvasH.value - 80) / Math.max(total, 1))
  const startY = (canvasH.value - (total - 1) * spacing) / 2
  return {
    left: `${canvasW.value / 2}px`,
    top: `${startY + idx * spacing}px`,
    transform: 'translate(-50%, -50%)'
  }
}

const supplyBusY = computed(() => {
  if (!isMultiBus.value) return busY.value
  const total = buses.value?.length ?? 1
  const spacing = Math.min(80, (canvasH.value - 80) / Math.max(total, 1))
  return (canvasH.value - (total - 1) * spacing) / 2
})

const demandBusY = computed(() => {
  if (!isMultiBus.value) return busY.value
  const total = buses.value?.length ?? 1
  const spacing = Math.min(80, (canvasH.value - 80) / Math.max(total, 1))
  return (canvasH.value - (total - 1) * spacing) / 2 + (total - 1) * spacing
})

// ── Card position styles ──────────────────────────────────────────────────────
function supplyCardStyle(i: number) {
  const { padX, cardH, gap } = lv.value
  if (isColumn.value) {
    return { left: `${padX}px`, top: `${COL_PAD_Y + i * (cardH + gap)}px`, width: `${colCardW.value}px` }
  }
  const total = props.supplies.length
  const totalH = total * cardH + (total - 1) * gap
  const top = (canvasH.value - totalH) / 2 + i * (cardH + gap)
  return { left: `${padX}px`, top: `${top}px`, width: `${lv.value.cardW}px` }
}

function demandCardStyle(i: number) {
  const { padX, cardH, gap } = lv.value
  if (isColumn.value) {
    return { left: `${padX}px`, top: `${colDemandStart.value + i * (cardH + gap)}px`, width: `${colCardW.value}px` }
  }
  const total = props.demands.length
  const totalH = total * cardH + (total - 1) * gap
  const top = (canvasH.value - totalH) / 2 + i * (cardH + gap)
  return { left: `${canvasW.value - padX - lv.value.cardW}px`, top: `${top}px`, width: `${lv.value.cardW}px` }
}

// ── Storage card positioning ──────────────────────────────────────────────────
function storageCardStyle(i: number) {
  const { cardH, gap } = lv.value
  const batCount = props.storage?.length ?? 0
  if (isColumn.value) {
    // Column mode: place batteries between bus and demands
    const batStartY = colBusStart.value + colBusBlockH.value + 8
    return { left: `${lv.value.padX}px`, top: `${batStartY + i * (cardH + gap)}px`, width: `${colCardW.value}px` }
  }
  // Horizontal mode: place batteries below the bus, centered
  const batW = Math.min(lv.value.cardW, 180)
  const _totalH = batCount * cardH + (batCount - 1) * gap
  const topStart = busY.value + busR.value + 24
  return {
    left: `${canvasW.value / 2 - batW / 2}px`,
    top: `${topStart + i * (cardH + gap)}px`,
    width: `${batW}px`
  }
}

// ── Power helpers ─────────────────────────────────────────────────────────────
const genT = computed(() => props.result?.result_json?.generators_t ?? {})
const loadT = computed(() => props.result?.result_json?.loads_t ?? {})
const storageT = computed(() => props.result?.result_json?.storage_units_t ?? {})
const avg = (s: number[]) => s.length ? s.reduce((a, v) => a + v, 0) / s.length : 0
const supplyAvg = (s: Supply) => {
  const ts = genT.value[s.name]
  return ts ? avg(ts.p) : s.capacity_mw
}
const demandAvg = (d: Demand) => {
  const ts = loadT.value[d.name]
  return ts ? avg(ts.p) : d.load_mw
}
const storageAvg = (s: Supply) => {
  const ts = storageT.value[s.name]
  return ts ? avg(ts.p) : 0
}
const fmtPow = (v: number) => v.toFixed(1)

// ── Cable lines ───────────────────────────────────────────────────────────────
const cableLines = computed<CableLine[]>(() => {
  if (canvasW.value === 0) return []
  const { padX, cardH, gap, cardW } = lv.value
  const r = busR.value
  const lines: CableLine[] = []

  if (isColumn.value) {
    const cx = canvasW.value / 2
    props.supplies.forEach((s, i) => {
      const power = supplyAvg(s)
      const cardBottom = COL_PAD_Y + i * (cardH + gap) + cardH
      lines.push({ x1: cx, y1: cardBottom, x2: busX.value, y2: busY.value - r,
        isSupply: true, isBusCable: false, power, label: props.result ? `${fmtPow(power)} MW` : '' })
    })
    props.demands.forEach((d, i) => {
      const power = demandAvg(d)
      const cardTop = colDemandStart.value + i * (cardH + gap)
      lines.push({ x1: busX.value, y1: busY.value + r, x2: cx, y2: cardTop,
        isSupply: false, isBusCable: false, power, label: props.result ? `${fmtPow(power)} MW` : '' })
    })
  } else {
    const total_s = props.supplies.length
    const total_d = props.demands.length
    props.supplies.forEach((s, i) => {
      const power = supplyAvg(s)
      const totalH = total_s * cardH + (total_s - 1) * gap
      const cardMidY = (canvasH.value - totalH) / 2 + i * (cardH + gap) + cardH / 2
      lines.push({ x1: padX + cardW, y1: cardMidY, x2: busX.value - r, y2: supplyBusY.value,
        isSupply: true, isBusCable: false, power, label: props.result ? `${fmtPow(power)} MW` : '' })
    })
    props.demands.forEach((d, i) => {
      const power = demandAvg(d)
      const totalH = total_d * cardH + (total_d - 1) * gap
      const cardMidY = (canvasH.value - totalH) / 2 + i * (cardH + gap) + cardH / 2
      lines.push({ x1: busX.value + r, y1: demandBusY.value, x2: canvasW.value - padX - cardW, y2: cardMidY,
        isSupply: false, isBusCable: false, power, label: props.result ? `${fmtPow(power)} MW` : '' })
    })

    // ── Inter-bus links (transformers / lines between consecutive buses) ──
    if (isMultiBus.value && buses.value && buses.value.length > 1) {
      const total = buses.value.length
      const spacing = Math.min(80, (canvasH.value - 80) / Math.max(total, 1))
      const startY = (canvasH.value - (total - 1) * spacing) / 2
      const cx = canvasW.value / 2
      const halfBus = multiBusSize.value / 2

      for (let idx = 0; idx < total - 1; idx++) {
        const y1 = startY + idx * spacing + halfBus
        const y2 = startY + (idx + 1) * spacing - halfBus
        // Find the network component connecting these two voltage levels
        const busA = buses.value[idx]
        const busB = buses.value[idx + 1]
        const nc = props.network.find((n) => {
          if (n.type === 'transformer') {
            const hvBus = `bus_${n.voltage_hv_kv}kV`
            const lvBus = `bus_${n.voltage_lv_kv}kV`
            return (hvBus === busA && lvBus === busB) || (hvBus === busB && lvBus === busA)
          }
          return false
        })
        const label = nc ? `${nc.name} (${nc.capacity_mva} MVA)` : ''
        lines.push({
          x1: cx, y1,
          x2: cx, y2,
          isSupply: false,
          isBusCable: true,
          power: nc?.capacity_mva ?? 0,
          label
        })
      }
    }
  }
  return lines
})

// ── Tooltip ───────────────────────────────────────────────────────────────────

interface TipRow { label: string, value: string, color?: string }
interface TipData {
  name: string
  typeLabel: string
  kind: 'supply' | 'demand' | 'network' | 'bus'
  params: TipRow[]
  results?: TipRow[]
  hint?: string
}

const tip = ref<{ visible: boolean, x: number, y: number, data: TipData | null }>({
  visible: false, x: 0, y: 0, data: null
})

const SUPPLY_HINTS: Record<string, string> = {
  wind_turbine: 'Output depends on wind speed. PyPSA scales capacity by an hourly weather factor (0–1) from KNMI data.',
  solar_panel: 'Output depends on solar irradiance. Zero at night, peaks around noon.',
  nuclear_plant: 'Dispatchable baseload — runs at a fixed fraction of capacity regardless of weather.'
}
const DEMAND_HINTS: Record<string, string> = {
  house: 'Residential load. Profile peaks in morning and evening, lower overnight.',
  electric_vehicle: 'EV charging load. Concentrated in evening/night hours.'
}
const NETWORK_HINTS: Record<string, string> = {
  transformer: 'Steps voltage up or down between buses. Loading % = actual MVA / rated MVA.',
  cable: 'Transmits power between buses. Overloading (>100%) indicates a thermal limit violation.'
}

const supplyMwh = (s: Supply) => {
  const ts = genT.value[s.name]
  return ts ? ts.p.reduce((a: number, v: number) => a + v, 0) : null
}
const demandMwh = (d: Demand) => {
  const ts = loadT.value[d.name]
  return ts ? ts.p.reduce((a: number, v: number) => a + v, 0) : null
}
const supplyCF = (s: Supply) => {
  const a = supplyAvg(s)
  return s.capacity_mw > 0 ? a / s.capacity_mw : 0
}

type AnyAsset = Supply | Demand | NetworkComponent | null

function buildTipData(kind: 'supply' | 'demand' | 'network' | 'bus', asset: AnyAsset): TipData {
  const r = props.result

  if (kind === 'supply' && asset && 'capacity_mw' in asset) {
    const s = asset as Supply
    const cf = supplyCF(s)
    const mwh = supplyMwh(s)
    const typeLabel = s.type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
    const results: TipRow[] = r
      ? [
          { label: 'Avg output', value: `${fmtPow(supplyAvg(s))} MW`, color: 'text-emerald-400' },
          { label: 'Capacity factor', value: `${(cf * 100).toFixed(1)} %`, color: cf < 0.2 ? 'text-amber-400' : 'text-emerald-400' },
          ...(mwh != null ? [{ label: 'Energy produced', value: `${mwh.toFixed(0)} MWh`, color: 'text-blue-300' }] : [])
        ]
      : []
    return {
      name: s.name, typeLabel, kind: 'supply',
      params: [
        { label: 'Installed capacity', value: `${s.capacity_mw} MW` },
        { label: 'Efficiency', value: `${(s.efficiency * 100).toFixed(0)} %` }
      ],
      results,
      hint: SUPPLY_HINTS[s.type] ?? 'Supply asset injecting power into the network.'
    }
  }

  if (kind === 'demand' && asset && 'load_mw' in asset) {
    const d = asset as Demand
    const mwh = demandMwh(d)
    const typeLabel = d.type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
    const results: TipRow[] = r
      ? [
          { label: 'Avg consumption', value: `${fmtPow(demandAvg(d))} MW`, color: 'text-red-400' },
          ...(mwh != null ? [{ label: 'Energy consumed', value: `${mwh.toFixed(0)} MWh`, color: 'text-blue-300' }] : [])
        ]
      : []
    return {
      name: d.name, typeLabel, kind: 'demand',
      params: [{ label: 'Peak load', value: `${d.load_mw} MW` }],
      results,
      hint: DEMAND_HINTS[d.type] ?? 'Load consuming power from the network.'
    }
  }

  if (kind === 'network' && asset && 'capacity_mva' in asset) {
    const n = asset as NetworkComponent
    const typeLabel = n.type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
    return {
      name: n.name, typeLabel, kind: 'network',
      params: [
        { label: 'Rated capacity', value: `${n.capacity_mva} MVA` },
        ...(n.voltage_kv != null ? [{ label: 'Voltage', value: `${n.voltage_kv} kV` }] : [])
      ],
      hint: NETWORK_HINTS[n.type] ?? 'Network component connecting buses.'
    }
  }

  // Bus
  const busResults: TipRow[] = r
    ? [
        { label: 'Status', value: (r.status === 'optimized' || r.status === 'optimal') ? 'Optimised' : r.status === 'converged' ? 'Converged' : r.status === 'non_converged' ? 'Non-converged' : r.status === 'infeasible' ? 'Infeasible' : 'Error', color: (r.status === 'converged' || r.status === 'optimized' || r.status === 'optimal') ? 'text-emerald-400' : 'text-red-400' },
        { label: 'Total supply', value: `${r.total_supply_mwh?.toFixed(0) ?? '—'} MWh`, color: 'text-emerald-400' },
        { label: 'Total demand', value: `${r.total_demand_mwh?.toFixed(0) ?? '—'} MWh`, color: 'text-red-400' },
        { label: 'Balance', value: `${r.balance_mwh != null ? (r.balance_mwh > 0 ? '+' : '') + r.balance_mwh.toFixed(0) : '—'} MWh`, color: r.balance_mwh != null && Math.abs(r.balance_mwh) < 0.1 ? 'text-emerald-400' : r.balance_mwh != null && r.balance_mwh > 0 ? 'text-blue-400' : 'text-amber-400' }
      ]
    : []

  // Multi-bus: asset is the bus name string
  if (isMultiBus.value && typeof asset === 'string') {
    const busName = asset as string
    const voltageLabel = formatBusName(busName)
    const busData = r?.result_json?.buses_t?.[busName]
    const mbResults: TipRow[] = [...busResults]
    if (busData?.marginal_price) {
      const prices = busData.marginal_price as number[]
      const avgPrice = prices.length ? prices.reduce((a: number, v: number) => a + v, 0) / prices.length : 0
      mbResults.push({ label: 'Avg marginal price', value: `${avgPrice.toFixed(2)} €/MWh`, color: 'text-blue-300' })
    }
    return {
      name: voltageLabel, typeLabel: 'Bus', kind: 'bus',
      params: [{ label: 'Bus ID', value: busName }, { label: 'Voltage', value: voltageLabel }],
      results: mbResults,
      hint: 'Bus node in multi-voltage topology. Connected via transformers and lines to other voltage levels.'
    }
  }

  return {
    name: 'Main Bus', typeLabel: '380 kV', kind: 'bus',
    params: [{ label: 'Voltage', value: '380 kV' }, { label: 'Type', value: 'AC bus (slack)' }],
    results: busResults,
    hint: 'Central bus connecting all generators, batteries, and loads. LOPF balances supply and demand optimally across all hours.'
  }
}

function showTooltip(kind: 'supply' | 'demand' | 'network' | 'bus', asset: AnyAsset, e: MouseEvent) {
  tip.value = {
    visible: true,
    x: e.clientX,
    y: e.clientY,
    data: buildTipData(kind, asset)
  }
}

function moveTooltip(e: MouseEvent) {
  if (!tip.value.visible) return
  tip.value.x = e.clientX
  tip.value.y = e.clientY
}

function hideTooltip() {
  tip.value.visible = false
}

const TIP_W = 224 // w-56 = 14rem = 224px
const TIP_OFFSET = 14

const tipScreenStyle = computed(() => {
  const x = tip.value.x
  const y = tip.value.y
  const vw = typeof window !== 'undefined' ? window.innerWidth : 1920
  const vh = typeof window !== 'undefined' ? window.innerHeight : 1080
  const flipX = x + TIP_OFFSET + TIP_W > vw
  const flipY = y + TIP_OFFSET + 260 > vh
  return {
    left: flipX ? `${x - TIP_W - TIP_OFFSET}px` : `${x + TIP_OFFSET}px`,
    top: flipY ? `${y - TIP_OFFSET - 10}px` : `${y + TIP_OFFSET}px`,
    transform: flipY ? 'translateY(-100%)' : 'none'
  }
})

const tipBadgeClass = computed(() => {
  const kind = tip.value.data?.kind
  if (kind === 'supply') return 'bg-amber-900/40 text-amber-300'
  if (kind === 'demand') return 'bg-emerald-900/40 text-emerald-300'
  if (kind === 'network') return 'bg-blue-900/40 text-blue-300'
  return 'bg-slate-800 text-slate-300'
})

// ── ResizeObserver + tab-visibility watcher ───────────────────────────────────
function readWidth() {
  if (canvasRef.value) {
    const w = canvasRef.value.clientWidth
    if (w > 0) canvasW.value = w
  }
}

let ro: ResizeObserver | null = null

onMounted(() => {
  if (canvasRef.value) {
    ro = new ResizeObserver((entries) => {
      if (entries[0]) canvasW.value = entries[0].contentRect.width
    })
    ro.observe(canvasRef.value)
    nextTick(readWidth)
  }
})

watch(() => props.visible, (val) => {
  if (val !== false) nextTick(() => requestAnimationFrame(readWidth))
})

onUnmounted(() => ro?.disconnect())

// ── Timestamp ─────────────────────────────────────────────────────────────────
const timestamp = computed(() => {
  if (!props.result) return ''
  const d = new Date(props.result.created_at)
  const p = (n: number) => String(n).padStart(2, '0')
  return `${p(d.getDate())}/${p(d.getMonth() + 1)}/${d.getFullYear()}, ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
})
</script>

<style scoped>
.tip-enter-active { transition: opacity 0.1s ease, transform 0.1s ease; }
.tip-leave-active { transition: opacity 0.08s ease; }
.tip-enter-from  { opacity: 0; transform: scale(0.97) translateY(4px); }
.tip-leave-to    { opacity: 0; }
</style>
