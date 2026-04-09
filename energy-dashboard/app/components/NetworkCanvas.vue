<template>
  <div
    ref="canvasRef"
    class="relative w-full bg-[#020617] rounded-2xl border border-[#1E293B] overflow-hidden"
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
      class="absolute bg-[#0B1220] border border-[#1E293B] rounded-xl flex items-center hover:border-[#334155] transition-colors duration-200"
      :class="lv.cardPad"
      :style="supplyCardStyle(i)"
    >
      <NetworkCanvasAssetIcon v-if="!isMicro" :type="supply.type" :size="lv.iconSize" class="shrink-0" />
      <div class="min-w-0 flex-1" :class="isMicro ? '' : lv.cardGap">
        <p class="font-semibold text-white truncate leading-tight" :class="lv.cardTitle">{{ supply.name }}</p>
        <p class="text-gray-500 leading-tight" :class="lv.cardSub">{{ supply.capacity_mw }} MW</p>
        <p v-if="result && !isMicro" class="font-mono text-emerald-400 leading-tight" :class="lv.cardSub">
          ⚡ {{ fmtPow(supplyAvg(supply)) }} MW avg
        </p>
        <p v-else-if="result && isMicro" class="font-mono text-emerald-400 leading-tight text-[9px]">
          {{ fmtPow(supplyAvg(supply)) }} MW
        </p>
      </div>
    </div>

    <!-- ── Demand cards ──────────────────────────────────────────────────── -->
    <div
      v-for="(demand, i) in demands"
      :key="demand.id"
      class="absolute bg-[#0B1220] border border-[#1E293B] rounded-xl flex items-center hover:border-[#334155] transition-colors duration-200"
      :class="lv.cardPad"
      :style="demandCardStyle(i)"
    >
      <NetworkCanvasAssetIcon v-if="!isMicro" :type="demand.type" :size="lv.iconSize" class="shrink-0" />
      <div class="min-w-0 flex-1" :class="isMicro ? '' : lv.cardGap">
        <p class="font-semibold text-white truncate leading-tight" :class="lv.cardTitle">{{ demand.name }}</p>
        <p class="text-gray-500 leading-tight" :class="lv.cardSub">{{ demand.load_mw }} MW</p>
        <p v-if="result && !isMicro" class="font-mono text-red-400 leading-tight" :class="lv.cardSub">
          🔌 {{ fmtPow(demandAvg(demand)) }} MW avg
        </p>
        <p v-else-if="result && isMicro" class="font-mono text-red-400 leading-tight text-[9px]">
          {{ fmtPow(demandAvg(demand)) }} MW
        </p>
      </div>
    </div>

    <!-- ── Bus node ──────────────────────────────────────────────────────── -->
    <div
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
        class="relative flex flex-col items-center justify-center rounded-full border-2 bg-[#0B1220]"
        :style="{ width: `${lv.busSize}px`, height: `${lv.busSize}px` }"
        :class="busBorderColor"
      >
        <svg :width="lv.busIconSize" :height="lv.busIconSize" viewBox="0 0 24 24" fill="none">
          <path d="M13 2L4.5 13.5H11L10 22L19.5 10.5H13L13 2Z" :fill="busIconFill" stroke="none" />
        </svg>
        <span v-if="!isCompact" class="text-[9px] text-gray-500 font-mono leading-none mt-0.5">380 kV</span>
      </div>
      <!-- Bus label -->
      <div class="mt-1.5 text-center" :style="{ maxWidth: `${lv.busSize + 40}px` }">
        <p class="font-semibold text-gray-400 truncate" :class="lv.busLabel">Main Bus</p>
        <p v-if="result" class="font-semibold mt-0.5" :class="[lv.busLabel, busStatusColor]">{{ busStatusLabel }}</p>
        <p v-else class="text-gray-700 mt-0.5" :class="lv.busLabel">No result</p>
      </div>
      <!-- Network component badges (full layout only) -->
      <div v-if="network.length && isFull" class="mt-3 flex flex-col gap-1.5 w-44">
        <div
          v-for="n in network"
          :key="n.id"
          class="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-[#0B1220] border border-[#1E293B] text-[11px]"
        >
          <NetworkCanvasAssetIcon :type="n.type" :size="18" />
          <span class="text-gray-400 truncate">{{ n.name }}</span>
          <span class="text-gray-600 font-mono ml-auto shrink-0">{{ n.capacity_mva }} MVA</span>
        </div>
      </div>
    </div>

    <!-- ── Timestamp ──────────────────────────────────────────────────────── -->
    <div v-if="result && isFull" class="absolute top-3 right-4 text-xs font-mono text-gray-600 select-none">
      {{ timestamp }}
    </div>

    <!-- ── Side / section labels ─────────────────────────────────────────── -->
    <template v-if="!isColumn">
      <div v-if="supplies.length" class="absolute top-3 left-4 text-[10px] font-semibold uppercase tracking-widest text-gray-700 select-none">
        Supply
      </div>
      <div v-if="demands.length" class="absolute top-3 text-[10px] font-semibold uppercase tracking-widest text-gray-700 select-none" :style="{ right: `${lv.padX + 2}px` }">
        Demand
      </div>
    </template>
    <template v-else>
      <div v-if="supplies.length" class="absolute text-[10px] font-semibold uppercase tracking-widest text-gray-700 select-none" :style="{ top: `${COL_PAD_Y - 14}px`, left: `${lv.padX}px` }">
        Supply
      </div>
      <div v-if="demands.length" class="absolute text-[10px] font-semibold uppercase tracking-widest text-gray-700 select-none" :style="{ top: `${colDemandStart - 14}px`, left: `${lv.padX}px` }">
        Demand
      </div>
    </template>

    <!-- ── Empty state ────────────────────────────────────────────────────── -->
    <div v-if="!supplies.length && !demands.length" class="absolute inset-0 flex items-center justify-center pointer-events-none">
      <p class="text-gray-700 text-sm text-center px-6">Add supply and demand assets to visualize the network</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Supply, Demand, NetworkComponent, SimulationResult } from '~/composables/api'
import NetworkCanvasCableLayer from '~/components/network-canvas/CableLayer.vue'
import NetworkCanvasAssetIcon  from '~/components/network-canvas/AssetIcon.vue'
import type { CableLine } from '~/components/network-canvas/CableLayer.vue'

const props = defineProps<{
  supplies: Supply[]
  demands:  Demand[]
  network:  NetworkComponent[]
  result:   SimulationResult | null
  visible?: boolean
}>()

// ── Canvas measure ────────────────────────────────────────────────────────────
const canvasRef = ref<HTMLElement | null>(null)
const canvasW   = ref(0)

// ── Responsive flags ──────────────────────────────────────────────────────────
const isColumn  = computed(() => canvasW.value > 0 && canvasW.value < 500)
const isMicro   = computed(() => canvasW.value > 0 && canvasW.value < 400)
const isCompact = computed(() => canvasW.value > 0 && canvasW.value < 650)
const isFull    = computed(() => canvasW.value >= 900)

// ── Layout values per breakpoint ──────────────────────────────────────────────
const lv = computed(() => {
  const w = canvasW.value
  if (w < 500) return {
    padX: w < 400 ? 6 : 10,
    cardW: 0, cardH: w < 400 ? 52 : 60, iconSize: w < 400 ? 0 : 28,
    busSize: w < 400 ? 52 : 64, busIconSize: w < 400 ? 18 : 22, gap: 8,
    cardPad: w < 400 ? 'p-1.5 gap-1' : 'p-2 gap-1.5', cardGap: w < 400 ? '' : 'ml-1.5',
    cardTitle: w < 400 ? 'text-[9px]' : 'text-[10px]', cardSub: w < 400 ? 'text-[9px]' : 'text-[10px]',
    busLabel: w < 400 ? 'text-[9px]' : 'text-[10px]',
  }
  if (w < 600) return {
    padX: 10, cardW: 130, cardH: 60, iconSize: 28, busSize: 60, busIconSize: 20, gap: 10,
    cardPad: 'p-2 gap-1.5', cardGap: 'ml-1.5', cardTitle: 'text-[10px]', cardSub: 'text-[10px]',
    busLabel: 'text-[10px]',
  }
  if (w < 800) return {
    padX: 16, cardW: 158, cardH: 68, iconSize: 36, busSize: 72, busIconSize: 24, gap: 12,
    cardPad: 'p-2 gap-2', cardGap: 'ml-2', cardTitle: 'text-[11px]', cardSub: 'text-[10px]',
    busLabel: 'text-[10px]',
  }
  if (w < 1100) return {
    padX: 22, cardW: 182, cardH: 76, iconSize: 44, busSize: 84, busIconSize: 30, gap: 14,
    cardPad: 'p-2.5 gap-2.5', cardGap: 'ml-2', cardTitle: 'text-xs', cardSub: 'text-[11px]',
    busLabel: 'text-[11px]',
  }
  return {
    padX: 28, cardW: 210, cardH: 82, iconSize: 52, busSize: 96, busIconSize: 36, gap: 14,
    cardPad: 'p-3 gap-3', cardGap: 'ml-1', cardTitle: 'text-xs', cardSub: 'text-[11px]',
    busLabel: 'text-xs',
  }
})

// ── Column-mode constants & derived heights ───────────────────────────────────
const COL_PAD_Y = 28
const COL_GAP   = 20

const colCardW        = computed(() => canvasW.value - 2 * lv.value.padX)
const colSupplyBlockH = computed(() => {
  const { cardH, gap } = lv.value
  const n = props.supplies.length
  return n ? n * cardH + (n - 1) * gap : 0
})
const colBusBlockH    = computed(() => lv.value.busSize + 28)
const colDemandBlockH = computed(() => {
  const { cardH, gap } = lv.value
  const n = props.demands.length
  return n ? n * cardH + (n - 1) * gap : 0
})
const colBusStart     = computed(() =>
  COL_PAD_Y + (props.supplies.length ? colSupplyBlockH.value + COL_GAP : 0)
)
const colDemandStart  = computed(() =>
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
const busOk          = computed(() => props.result?.status === 'converged')
const busGlowColor   = computed(() => !props.result ? 'bg-gray-600' : busOk.value ? 'bg-emerald-500' : 'bg-red-500')
const busBorderColor = computed(() => !props.result ? 'border-[#334155]' : busOk.value ? 'border-emerald-600/60' : 'border-red-600/60')
const busIconFill    = computed(() => !props.result ? '#475569' : busOk.value ? '#34d399' : '#f87171')
const busStatusColor = computed(() => !props.result ? 'text-gray-600' : busOk.value ? 'text-emerald-400' : 'text-red-400')
const busStatusLabel = computed(() => {
  if (!props.result) return ''
  return props.result.status === 'converged' ? 'Converged'
    : props.result.status === 'non_converged' ? 'Non-conv.'
    : 'Error'
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

// ── Power helpers ─────────────────────────────────────────────────────────────
const genT  = computed(() => props.result?.result_json?.generators_t ?? {})
const loadT = computed(() => props.result?.result_json?.loads_t      ?? {})
const avg   = (s: number[]) => s.length ? s.reduce((a, v) => a + v, 0) / s.length : 0
const supplyAvg = (s: Supply) => { const ts = genT.value[s.name];  return ts ? avg(ts.p) : s.capacity_mw }
const demandAvg = (d: Demand) => { const ts = loadT.value[d.name]; return ts ? avg(ts.p) : d.load_mw }
const fmtPow    = (v: number) => v.toFixed(1)

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
      lines.push({ x1: padX + cardW, y1: cardMidY, x2: busX.value - r, y2: busY.value,
        isSupply: true, isBusCable: false, power, label: props.result ? `${fmtPow(power)} MW` : '' })
    })
    props.demands.forEach((d, i) => {
      const power = demandAvg(d)
      const totalH = total_d * cardH + (total_d - 1) * gap
      const cardMidY = (canvasH.value - totalH) / 2 + i * (cardH + gap) + cardH / 2
      lines.push({ x1: busX.value + r, y1: busY.value, x2: canvasW.value - padX - cardW, y2: cardMidY,
        isSupply: false, isBusCable: false, power, label: props.result ? `${fmtPow(power)} MW` : '' })
    })
  }
  return lines
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
    ro = new ResizeObserver(([e]) => { canvasW.value = e.contentRect.width })
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
