<template>
  <div class="border-t border-slate-800 p-2 space-y-2 bg-slate-950">
    <div class="flex items-center justify-between mb-1">
      <p class="text-xs text-gray-500 uppercase tracking-wider">
        Parameters
      </p>
      <!-- Live preview indicator -->
      <span
        v-if="store.isLiveRunning"
        class="inline-flex items-center gap-1 text-[10px] text-blue-400"
      >
        <span class="relative flex h-2 w-2">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
          <span class="relative inline-flex rounded-full h-2 w-2 bg-blue-500" />
        </span>
        Live preview
      </span>
    </div>

    <!-- Supply fields -->
    <template v-if="groupType === 'supply' && 'capacity_mw' in asset">
      <div>
        <label class="text-xs text-gray-400 flex items-center gap-1 mb-0.5">
          Capacity (MW)
          <UTooltip text="Installed capacity in MW — the maximum power this generator can inject at any given moment. For wind/solar, PyPSA multiplies this by the hourly weather capacity factor (0–1), so actual output varies with weather conditions.">
            <UIcon
              name="i-heroicons-information-circle"
              class="w-3.5 h-3.5 text-gray-600 cursor-help shrink-0"
            />
          </UTooltip>
        </label>
        <UInput
          :model-value="getVal('capacity_mw', (asset as Supply).capacity_mw)"
          type="number"
          size="xs"
          @update:model-value="setVal('capacity_mw', $event)"
        />
        <input
          type="range"
          :value="getVal('capacity_mw', (asset as Supply).capacity_mw)"
          min="0"
          max="5000"
          step="10"
          class="w-full h-2 rounded-lg appearance-none cursor-pointer bg-slate-700 accent-blue-500 mt-1"
          @input="setVal('capacity_mw', ($event.target as HTMLInputElement).value)"
        >
      </div>
      <div>
        <label class="text-xs text-gray-400 flex items-center gap-1 mb-0.5">
          Efficiency (0–1)
          <UTooltip text="Conversion efficiency from fuel to electricity. For nuclear plants, this reduces effective output (e.g. 0.33 means only 33% of thermal power becomes electricity). Wind and solar efficiencies are already embedded in the KNMI weather profile.">
            <UIcon
              name="i-heroicons-information-circle"
              class="w-3.5 h-3.5 text-gray-600 cursor-help shrink-0"
            />
          </UTooltip>
        </label>
        <UInput
          :model-value="getVal('efficiency', (asset as Supply).efficiency)"
          type="number"
          step="0.01"
          size="xs"
          @update:model-value="setVal('efficiency', $event)"
        />
        <input
          type="range"
          :value="getVal('efficiency', (asset as Supply).efficiency)"
          min="0"
          max="1"
          step="0.01"
          class="w-full h-2 rounded-lg appearance-none cursor-pointer bg-slate-700 accent-blue-500 mt-1"
          @input="setVal('efficiency', ($event.target as HTMLInputElement).value)"
        >
      </div>
    </template>

    <!-- Demand fields -->
    <template v-if="groupType === 'demand' && 'load_mw' in asset">
      <div>
        <label class="text-xs text-gray-400 flex items-center gap-1 mb-0.5">
          Load (MW)
          <UTooltip text="Peak consumption in MW for this demand node. PyPSA scales this by a normalised hourly load profile (0–1) derived from historical patterns, so each hour gets a fraction of this peak value.">
            <UIcon
              name="i-heroicons-information-circle"
              class="w-3.5 h-3.5 text-gray-600 cursor-help shrink-0"
            />
          </UTooltip>
        </label>
        <UInput
          :model-value="getVal('load_mw', (asset as Demand).load_mw)"
          type="number"
          size="xs"
          @update:model-value="setVal('load_mw', $event)"
        />
        <input
          type="range"
          :value="getVal('load_mw', (asset as Demand).load_mw)"
          min="0"
          max="1000"
          step="5"
          class="w-full h-2 rounded-lg appearance-none cursor-pointer bg-slate-700 accent-blue-500 mt-1"
          @input="setVal('load_mw', ($event.target as HTMLInputElement).value)"
        >
      </div>
    </template>

    <!-- Network fields -->
    <template v-if="groupType === 'network' && 'capacity_mva' in asset">
      <div>
        <label class="text-xs text-gray-400 flex items-center gap-1 mb-0.5">
          Capacity (MVA)
          <UTooltip text="Apparent power rating of this network component in MVA. PyPSA uses this to compute the line loading percentage shown in the Network tab. Exceeding 100% loading means the line is overloaded.">
            <UIcon
              name="i-heroicons-information-circle"
              class="w-3.5 h-3.5 text-gray-600 cursor-help shrink-0"
            />
          </UTooltip>
        </label>
        <UInput
          :model-value="getVal('capacity_mva', (asset as NetworkComponent).capacity_mva)"
          type="number"
          size="xs"
          @update:model-value="setVal('capacity_mva', $event)"
        />
        <input
          type="range"
          :value="getVal('capacity_mva', (asset as NetworkComponent).capacity_mva)"
          min="0"
          max="2000"
          step="10"
          class="w-full h-2 rounded-lg appearance-none cursor-pointer bg-slate-700 accent-blue-500 mt-1"
          @input="setVal('capacity_mva', ($event.target as HTMLInputElement).value)"
        >
      </div>
    </template>

    <button
      v-if="store.hasOverrides(groupType, asset.id)"
      class="text-xs text-gray-500 hover:text-gray-300 mt-1"
      @click="store.clearOverrides(groupType, asset.id)"
    >
      ↺ Reset
    </button>
  </div>
</template>

<script setup lang="ts">
import { useSimulationStore } from '~/stores/simulation'
import type { Supply, Demand, NetworkComponent } from '~/composables/api'

const props = defineProps<{
  asset: Supply | Demand | NetworkComponent
  groupType: 'supply' | 'demand' | 'network'
}>()

const store = useSimulationStore()

function getVal(field: string, defaultVal: number): number {
  const overrides = store.getOverrides(props.groupType, props.asset.id)
  return field in overrides ? overrides[field] ?? defaultVal : defaultVal
}

function setVal(field: string, rawValue: string | number) {
  const value = typeof rawValue === 'string' ? parseFloat(rawValue) : rawValue
  if (!isNaN(value)) {
    store.setOverride(props.groupType, props.asset.id, field, value)
  }
}
</script>
