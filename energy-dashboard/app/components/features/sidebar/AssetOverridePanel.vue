<template>
  <div class="border-t border-[#1E293B] p-2 space-y-2 bg-[#0a111e]">
    <p class="text-xs text-gray-500 uppercase tracking-wider mb-1">
      Parameters
    </p>

    <!-- Supply fields -->
    <template v-if="groupType === 'supply' && 'capacity_mw' in asset">
      <div>
        <label class="text-xs text-gray-400 block mb-0.5">Capacity (MW)</label>
        <UInput
          :model-value="getVal('capacity_mw', (asset as Supply).capacity_mw)"
          type="number"
          size="xs"
          @update:model-value="setVal('capacity_mw', $event)"
        />
      </div>
      <div>
        <label class="text-xs text-gray-400 block mb-0.5">Efficiency (0–1)</label>
        <UInput
          :model-value="getVal('efficiency', (asset as Supply).efficiency)"
          type="number"
          step="0.01"
          size="xs"
          @update:model-value="setVal('efficiency', $event)"
        />
      </div>
    </template>

    <!-- Demand fields -->
    <template v-if="groupType === 'demand' && 'load_mw' in asset">
      <div>
        <label class="text-xs text-gray-400 block mb-0.5">Load (MW)</label>
        <UInput
          :model-value="getVal('load_mw', (asset as Demand).load_mw)"
          type="number"
          size="xs"
          @update:model-value="setVal('load_mw', $event)"
        />
      </div>
    </template>

    <!-- Network fields -->
    <template v-if="groupType === 'network' && 'capacity_mva' in asset">
      <div>
        <label class="text-xs text-gray-400 block mb-0.5">Capacity (MVA)</label>
        <UInput
          :model-value="getVal('capacity_mva', (asset as NetworkComponent).capacity_mva)"
          type="number"
          size="xs"
          @update:model-value="setVal('capacity_mva', $event)"
        />
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
  return field in overrides ? overrides[field] : defaultVal
}

function setVal(field: string, rawValue: string | number) {
  const value = typeof rawValue === 'string' ? parseFloat(rawValue) : rawValue
  if (!isNaN(value)) {
    if (!store.isLiveMode) store.selectedHistoryId = null
    store.setOverride(props.groupType, props.asset.id, field, value)
  }
}
</script>
