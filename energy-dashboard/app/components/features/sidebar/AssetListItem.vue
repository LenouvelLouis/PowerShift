<template>
  <div
    class="rounded-lg bg-[#020617] border overflow-hidden"
    :class="expanded ? 'border-[#3C83F8]/50' : 'border-[#1E293B]'"
  >
    <div
      class="p-2 cursor-pointer select-none"
      @click="$emit('toggle-expand')"
    >
      <div class="flex items-start justify-between gap-1">
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-1.5 flex-wrap">
            <UiAssetTypeIcon
              :type="asset.type"
              size="xs"
            />
            <p class="text-xs font-semibold text-white truncate">
              {{ asset.name }}
            </p>
            <span
              v-if="hasOverrides"
              class="text-xs px-1 py-0.5 bg-amber-900/40 text-amber-400 rounded leading-none"
            >Edited</span>
          </div>
          <p class="text-xs text-gray-500 mt-0.5 truncate">
            {{ summary }}
          </p>
        </div>
        <UIcon
          :name="expanded ? 'i-heroicons-chevron-up' : 'i-heroicons-chevron-down'"
          class="w-3 h-3 text-gray-600 shrink-0 mt-0.5"
        />
        <button
          class="text-red-400 hover:text-red-300 shrink-0 mt-0.5"
          @click.stop="$emit('remove')"
        >
          <UIcon
            name="i-heroicons-x-mark"
            class="w-3 h-3"
          />
        </button>
      </div>
    </div>
    <slot v-if="expanded" />
  </div>
</template>

<script setup lang="ts">
import type { Supply, Demand, NetworkComponent } from '~/composables/api'

defineProps<{
  asset: Supply | Demand | NetworkComponent
  expanded: boolean
  hasOverrides: boolean
  summary: string
}>()

defineEmits<{
  'toggle-expand': []
  'remove': []
}>()
</script>
