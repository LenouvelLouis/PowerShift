<template>
  <svg
    class="absolute inset-0 pointer-events-none"
    :width="canvasW"
    :height="canvasH"
    :viewBox="`0 0 ${canvasW} ${canvasH}`"
    xmlns="http://www.w3.org/2000/svg"
    style="z-index: 10; overflow: visible;"
  >
    <defs>
      <!-- Supply arrowhead (green, points toward bus) -->
      <marker
        id="arr-supply"
        markerWidth="8"
        markerHeight="8"
        refX="7"
        refY="4"
        orient="auto"
      >
        <path
          d="M0,1 L7,4 L0,7 Z"
          fill="#22c55e"
          opacity="0.9"
        />
      </marker>
      <!-- Demand arrowhead (red, points toward card) -->
      <marker
        id="arr-demand"
        markerWidth="8"
        markerHeight="8"
        refX="7"
        refY="4"
        orient="auto"
      >
        <path
          d="M0,1 L7,4 L0,7 Z"
          fill="#ef4444"
          opacity="0.9"
        />
      </marker>
      <!-- Bus-to-bus arrowhead (gray) -->
      <marker
        id="arr-bus"
        markerWidth="8"
        markerHeight="8"
        refX="7"
        refY="4"
        orient="auto"
      >
        <path
          d="M0,1 L7,4 L0,7 Z"
          fill="#64748b"
          opacity="0.9"
        />
      </marker>

      <!-- Glow filter for supply -->
      <filter
        id="glow-s"
        x="-50%"
        y="-50%"
        width="200%"
        height="200%"
      >
        <feGaussianBlur
          in="SourceGraphic"
          stdDeviation="3"
          result="blur"
        />
        <feComposite
          in="SourceGraphic"
          in2="blur"
          operator="over"
        />
      </filter>

      <!-- Glow filter for demand -->
      <filter
        id="glow-d"
        x="-50%"
        y="-50%"
        width="200%"
        height="200%"
      >
        <feGaussianBlur
          in="SourceGraphic"
          stdDeviation="3"
          result="blur"
        />
        <feComposite
          in="SourceGraphic"
          in2="blur"
          operator="over"
        />
      </filter>
    </defs>

    <!-- ── Glow halos ────────────────────────────────────────────────────── -->
    <line
      v-for="(ln, i) in lines"
      :key="`glow-${i}`"
      :x1="ln.x1"
      :y1="ln.y1"
      :x2="ln.x2"
      :y2="ln.y2"
      :stroke="ln.isBusCable ? '#64748b' : ln.isSupply ? '#22c55e' : '#ef4444'"
      :stroke-width="ln.isBusCable ? 18 : 12"
      stroke-linecap="round"
      :opacity="ln.isBusCable ? 0.1 : 0.15"
    />

    <!-- ── Solid base line ───────────────────────────────────────────────── -->
    <line
      v-for="(ln, i) in lines"
      :key="`base-${i}`"
      :x1="ln.x1"
      :y1="ln.y1"
      :x2="ln.x2"
      :y2="ln.y2"
      :stroke="ln.isBusCable ? '#334155' : ln.isSupply ? '#166534' : '#7f1d1d'"
      :stroke-width="ln.isBusCable ? 4 : 2"
      stroke-linecap="round"
      opacity="0.6"
    />

    <!-- ── Animated dashed cables ────────────────────────────────────────── -->
    <line
      v-for="(ln, i) in lines"
      :key="`cable-${i}`"
      :x1="ln.x1"
      :y1="ln.y1"
      :x2="ln.x2"
      :y2="ln.y2"
      :stroke="ln.isBusCable ? '#64748b' : ln.isSupply ? '#22c55e' : '#ef4444'"
      :stroke-width="ln.isBusCable ? 5 : 3"
      stroke-linecap="round"
      :stroke-dasharray="ln.isBusCable ? '14 6' : '10 5'"
      :marker-end="ln.isBusCable ? 'url(#arr-bus)' : ln.isSupply ? 'url(#arr-supply)' : 'url(#arr-demand)'"
      opacity="0.9"
      class="flow-anim"
      :style="{ '--dur': `${animDur(ln.power)}s` }"
    />

    <!-- ── Power labels at cable midpoints ───────────────────────────────── -->
    <template
      v-for="(ln, i) in lines"
      :key="`label-${i}`"
    >
      <template v-if="ln.label">
        <!-- Badge background -->
        <rect
          :x="mx(ln) - lblW(ln.label) / 2"
          :y="my(ln) - 10"
          :width="lblW(ln.label)"
          height="18"
          rx="6"
          fill="rgba(2,6,23,0.88)"
          stroke="rgba(51,65,85,0.7)"
          stroke-width="1"
        />
        <!-- Badge text -->
        <text
          :x="mx(ln)"
          :y="my(ln) + 5"
          text-anchor="middle"
          fill="white"
          font-size="10"
          font-family="ui-monospace,SFMono-Regular,monospace"
          opacity="0.95"
        >{{ ln.label }}</text>
      </template>
    </template>
  </svg>
</template>

<script setup lang="ts">
export interface CableLine {
  x1: number
  y1: number
  x2: number
  y2: number
  isSupply: boolean
  isBusCable: boolean // true = inter-bus line (thick, neutral gray)
  power: number
  label: string
}

defineProps<{
  lines: CableLine[]
  canvasW: number
  canvasH: number
}>()

function mx(ln: CableLine) {
  return (ln.x1 + ln.x2) / 2
}
function my(ln: CableLine) {
  return (ln.y1 + ln.y2) / 2
}

// Label badge width: ~6.4px per character + 14px horizontal padding
function lblW(label: string) {
  return label.length * 6.4 + 14
}

// Higher power → faster animation (min 0.4s, max 3s)
function animDur(power: number) {
  return Math.max(0.4, Math.min(3, 3 - power / 180))
}
</script>

<style scoped>
@keyframes flow {
  from { stroke-dashoffset: 45; }
  to   { stroke-dashoffset: 0; }
}

.flow-anim {
  animation: flow var(--dur, 1.4s) linear infinite;
}
</style>
