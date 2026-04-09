<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 72 72"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    class="shrink-0"
  >
    <!-- ── Solar panel ────────────────────────────────────────────────────── -->
    <template v-if="type === 'solar_panel'">
      <!-- Sun glow -->
      <circle cx="58" cy="13" r="10" fill="#fbbf24" opacity="0.15" />
      <!-- Sun circle -->
      <circle cx="58" cy="13" r="6" fill="#fbbf24" />
      <!-- Sun rays (8 directions) -->
      <line x1="58" y1="3"   x2="58" y2="5"   stroke="#fbbf24" stroke-width="2"   stroke-linecap="round" />
      <line x1="58" y1="21"  x2="58" y2="23"  stroke="#fbbf24" stroke-width="2"   stroke-linecap="round" />
      <line x1="48" y1="13"  x2="46" y2="13"  stroke="#fbbf24" stroke-width="2"   stroke-linecap="round" />
      <line x1="68" y1="13"  x2="70" y2="13"  stroke="#fbbf24" stroke-width="2"   stroke-linecap="round" />
      <line x1="50.8" y1="5.8"   x2="49.4" y2="4.4"   stroke="#fbbf24" stroke-width="1.5" stroke-linecap="round" />
      <line x1="65.2" y1="20.2"  x2="66.6" y2="21.6"  stroke="#fbbf24" stroke-width="1.5" stroke-linecap="round" />
      <line x1="65.2" y1="5.8"   x2="66.6" y2="4.4"   stroke="#fbbf24" stroke-width="1.5" stroke-linecap="round" />
      <line x1="50.8" y1="20.2"  x2="49.4" y2="21.6"  stroke="#fbbf24" stroke-width="1.5" stroke-linecap="round" />
      <!-- Panel body -->
      <rect x="4" y="24" width="52" height="30" rx="2" fill="#1e3a5f" stroke="#3b82f6" stroke-width="1.5" />
      <!-- Panel cell grid (3×2) -->
      <line x1="21.3" y1="24" x2="21.3" y2="54" stroke="#3b82f6" stroke-width="0.8" opacity="0.65" />
      <line x1="38.7" y1="24" x2="38.7" y2="54" stroke="#3b82f6" stroke-width="0.8" opacity="0.65" />
      <line x1="4"    y1="39" x2="56"   y2="39"  stroke="#3b82f6" stroke-width="0.8" opacity="0.65" />
      <!-- Cell fills -->
      <rect x="5.5"  y="25.5" width="14" height="12" rx="1" fill="#2563eb" opacity="0.25" />
      <rect x="22.8" y="25.5" width="14" height="12" rx="1" fill="#2563eb" opacity="0.25" />
      <rect x="40.2" y="25.5" width="14" height="12" rx="1" fill="#2563eb" opacity="0.25" />
      <rect x="5.5"  y="40.5" width="14" height="12" rx="1" fill="#2563eb" opacity="0.18" />
      <rect x="22.8" y="40.5" width="14" height="12" rx="1" fill="#2563eb" opacity="0.18" />
      <rect x="40.2" y="40.5" width="14" height="12" rx="1" fill="#2563eb" opacity="0.18" />
      <!-- Stand legs -->
      <line x1="16" y1="54" x2="10" y2="68" stroke="#475569" stroke-width="2.5" stroke-linecap="round" />
      <line x1="44" y1="54" x2="50" y2="68" stroke="#475569" stroke-width="2.5" stroke-linecap="round" />
      <line x1="8"  y1="68" x2="52" y2="68" stroke="#475569" stroke-width="2.5" stroke-linecap="round" />
    </template>

    <!-- ── Wind turbine ──────────────────────────────────────────────────── -->
    <template v-else-if="type === 'wind_turbine'">
      <!-- Tower (tapered) -->
      <polygon points="33,20 39,20 41,68 31,68" fill="#60a5fa" opacity="0.85" />
      <!-- Base -->
      <rect x="27" y="65" width="18" height="5" rx="2" fill="#3b82f6" />
      <!-- Hub -->
      <circle cx="36" cy="20" r="5.5" fill="#93c5fd" stroke="#3b82f6" stroke-width="1.5" />
      <!-- Blade 1 (up) -->
      <path d="M36,20 C33,14 34,7 36,5 C39,7 39,14 36,20 Z" fill="#3b82f6" opacity="0.9" />
      <!-- Blade 2 (bottom-right, 120°) -->
      <path d="M36,20 C33,14 34,7 36,5 C39,7 39,14 36,20 Z" fill="#3b82f6" opacity="0.9" transform="rotate(120 36 20)" />
      <!-- Blade 3 (bottom-left, 240°) -->
      <path d="M36,20 C33,14 34,7 36,5 C39,7 39,14 36,20 Z" fill="#3b82f6" opacity="0.9" transform="rotate(240 36 20)" />
      <!-- Hub center dot -->
      <circle cx="36" cy="20" r="2.5" fill="#eff6ff" />
    </template>

    <!-- ── Nuclear plant ─────────────────────────────────────────────────── -->
    <template v-else-if="type === 'nuclear_plant'">
      <!-- Glow -->
      <circle cx="36" cy="36" r="28" fill="#7c3aed" opacity="0.08" />
      <!-- Orbits -->
      <ellipse cx="36" cy="36" rx="28" ry="10" stroke="#8b5cf6" stroke-width="1.4" fill="none" />
      <ellipse cx="36" cy="36" rx="28" ry="10" stroke="#8b5cf6" stroke-width="1.4" fill="none" transform="rotate(60 36 36)" />
      <ellipse cx="36" cy="36" rx="28" ry="10" stroke="#8b5cf6" stroke-width="1.4" fill="none" transform="rotate(120 36 36)" />
      <!-- Electron dots -->
      <circle cx="64" cy="36"    r="3" fill="#c4b5fd" />
      <circle cx="21" cy="22.4"  r="3" fill="#c4b5fd" />
      <circle cx="21" cy="49.6"  r="3" fill="#c4b5fd" />
      <!-- Nucleus -->
      <circle cx="36" cy="36" r="9"   fill="#4c1d95" stroke="#a78bfa" stroke-width="1.5" />
      <circle cx="36" cy="36" r="5"   fill="#7c3aed" />
      <circle cx="33" cy="33" r="1.5" fill="#c4b5fd" opacity="0.7" />
      <circle cx="39" cy="37" r="1.5" fill="#c4b5fd" opacity="0.7" />
    </template>

    <!-- ── House ─────────────────────────────────────────────────────────── -->
    <template v-else-if="type === 'house'">
      <!-- Chimney (behind roof) -->
      <rect x="44" y="16" width="9" height="18" rx="1.5" fill="#1e40af" stroke="#60a5fa" stroke-width="1" />
      <!-- Smoke puffs -->
      <circle cx="48.5" cy="11" r="3.5" fill="#334155" opacity="0.55" />
      <circle cx="52"   cy="7.5" r="2.5" fill="#334155" opacity="0.35" />
      <!-- Roof -->
      <polygon points="5,36 36,10 67,36" fill="#1d4ed8" stroke="#60a5fa" stroke-width="1.5" stroke-linejoin="round" />
      <!-- Roof ridge accent -->
      <line x1="36" y1="10" x2="36" y2="36" stroke="#3b82f6" stroke-width="0.5" opacity="0.5" />
      <!-- House body -->
      <rect x="10" y="35" width="52" height="32" rx="2" fill="#1e40af" stroke="#60a5fa" stroke-width="1.5" />
      <!-- Door -->
      <rect x="30" y="49" width="12" height="18" rx="2" fill="#0f172a" stroke="#60a5fa" stroke-width="1" />
      <circle cx="39.5" cy="58" r="1.5" fill="#60a5fa" />
      <!-- Left window -->
      <rect x="13" y="40" width="11" height="10" rx="1.5" fill="#0f172a" stroke="#60a5fa" stroke-width="1" />
      <line x1="18.5" y1="40" x2="18.5" y2="50" stroke="#60a5fa" stroke-width="0.7" />
      <line x1="13"   y1="45" x2="24"   y2="45" stroke="#60a5fa" stroke-width="0.7" />
      <!-- Right window -->
      <rect x="48" y="40" width="11" height="10" rx="1.5" fill="#0f172a" stroke="#60a5fa" stroke-width="1" />
      <line x1="53.5" y1="40" x2="53.5" y2="50" stroke="#60a5fa" stroke-width="0.7" />
      <line x1="48"   y1="45" x2="59"   y2="45" stroke="#60a5fa" stroke-width="0.7" />
    </template>

    <!-- ── EV charger ─────────────────────────────────────────────────────── -->
    <template v-else-if="type === 'electric_vehicle'">
      <!-- Station body -->
      <rect x="14" y="6" width="32" height="44" rx="4" fill="#4c1d95" stroke="#8b5cf6" stroke-width="1.5" />
      <!-- Display screen -->
      <rect x="19" y="11" width="22" height="14" rx="2" fill="#0f172a" stroke="#7c3aed" stroke-width="1" />
      <!-- Battery progress bar on screen -->
      <rect x="21" y="21" width="18" height="3" rx="1.5" fill="#1e293b" />
      <rect x="21" y="21" width="13" height="3" rx="1.5" fill="#10b981" />
      <!-- Lightning bolt emblem -->
      <path d="M32,29 L37,24 L37,30 L42,30 L37,36 L37,30 Z" fill="#a78bfa" />
      <!-- Pole -->
      <rect x="29" y="50" width="12" height="16" rx="2" fill="#5b21b6" />
      <!-- Base platform -->
      <rect x="22" y="63" width="26" height="7" rx="3" fill="#4c1d95" stroke="#8b5cf6" stroke-width="1" />
      <!-- Cable (right side) -->
      <path d="M46,22 Q57,22 57,31 Q57,42 50,43" fill="none" stroke="#7c3aed" stroke-width="2.5" stroke-linecap="round" />
      <!-- Plug head -->
      <rect x="46" y="40" width="8" height="10" rx="2" fill="#5b21b6" stroke="#8b5cf6" stroke-width="1" />
      <line x1="49" y1="43" x2="49" y2="47" stroke="#a78bfa" stroke-width="1.5" stroke-linecap="round" />
      <line x1="53" y1="43" x2="53" y2="47" stroke="#a78bfa" stroke-width="1.5" stroke-linecap="round" />
    </template>

    <!-- ── Cable ──────────────────────────────────────────────────────────── -->
    <template v-else-if="type === 'cable'">
      <circle cx="14" cy="36" r="10" fill="none" stroke="#64748b" stroke-width="2" />
      <circle cx="14" cy="36" r="5"  fill="#334155" />
      <circle cx="58" cy="36" r="10" fill="none" stroke="#64748b" stroke-width="2" />
      <circle cx="58" cy="36" r="5"  fill="#334155" />
      <line x1="24" y1="36" x2="48" y2="36" stroke="#64748b" stroke-width="3" stroke-linecap="round" />
      <circle cx="36" cy="36" r="4" fill="none" stroke="#64748b" stroke-width="1.5" />
    </template>

    <!-- ── Transformer ────────────────────────────────────────────────────── -->
    <template v-else-if="type === 'transformer'">
      <!-- Iron core -->
      <rect x="30" y="9" width="12" height="48" rx="2" fill="#431407" stroke="#f97316" stroke-width="1" />
      <!-- Primary coil (left side) -->
      <path d="M6,18 Q6,12 16,12 Q26,12 26,18"  stroke="#fb923c" stroke-width="2" fill="none" stroke-linecap="round" />
      <path d="M6,24 Q6,18 16,18 Q26,18 26,24"  stroke="#fb923c" stroke-width="2" fill="none" stroke-linecap="round" />
      <path d="M6,30 Q6,24 16,24 Q26,24 26,30"  stroke="#fb923c" stroke-width="2" fill="none" stroke-linecap="round" />
      <path d="M6,36 Q6,30 16,30 Q26,30 26,36"  stroke="#fb923c" stroke-width="2" fill="none" stroke-linecap="round" />
      <path d="M6,42 Q6,36 16,36 Q26,36 26,42"  stroke="#fb923c" stroke-width="2" fill="none" stroke-linecap="round" />
      <path d="M6,48 Q6,42 16,42 Q26,42 26,48"  stroke="#fb923c" stroke-width="2" fill="none" stroke-linecap="round" />
      <!-- Primary leads -->
      <line x1="16" y1="12" x2="16" y2="6"  stroke="#f97316" stroke-width="2" stroke-linecap="round" />
      <line x1="16" y1="48" x2="16" y2="54" stroke="#f97316" stroke-width="2" stroke-linecap="round" />
      <!-- Secondary coil (right side) -->
      <path d="M42,18 Q42,12 52,12 Q62,12 62,18"  stroke="#fb923c" stroke-width="2" fill="none" stroke-linecap="round" />
      <path d="M42,24 Q42,18 52,18 Q62,18 62,24"  stroke="#fb923c" stroke-width="2" fill="none" stroke-linecap="round" />
      <path d="M42,30 Q42,24 52,24 Q62,24 62,30"  stroke="#fb923c" stroke-width="2" fill="none" stroke-linecap="round" />
      <path d="M42,36 Q42,30 52,30 Q62,30 62,36"  stroke="#fb923c" stroke-width="2" fill="none" stroke-linecap="round" />
      <path d="M42,42 Q42,36 52,36 Q62,36 62,42"  stroke="#fb923c" stroke-width="2" fill="none" stroke-linecap="round" />
      <path d="M42,48 Q42,42 52,42 Q62,42 62,48"  stroke="#fb923c" stroke-width="2" fill="none" stroke-linecap="round" />
      <!-- Secondary leads -->
      <line x1="52" y1="12" x2="52" y2="6"  stroke="#f97316" stroke-width="2" stroke-linecap="round" />
      <line x1="52" y1="48" x2="52" y2="54" stroke="#f97316" stroke-width="2" stroke-linecap="round" />
      <!-- HV / LV labels -->
      <text x="16" y="64" text-anchor="middle" fill="#f97316" font-size="8" font-family="monospace">HV</text>
      <text x="52" y="64" text-anchor="middle" fill="#f97316" font-size="8" font-family="monospace">LV</text>
    </template>

    <!-- ── Default fallback ────────────────────────────────────────────────── -->
    <template v-else>
      <circle cx="36" cy="36" r="28" fill="#1e293b" stroke="#475569" stroke-width="1.5" />
      <text x="36" y="41" text-anchor="middle" fill="#64748b" font-size="20" font-family="sans-serif">?</text>
    </template>
  </svg>
</template>

<script setup lang="ts">
defineProps<{
  type: string
  size?: number
}>()
</script>
