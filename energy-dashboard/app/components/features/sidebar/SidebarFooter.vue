<template>
  <div class="border-t border-slate-800 p-3 flex flex-col gap-2 shrink-0">
    <div class="text-xs text-gray-600 text-center font-mono">
      {{ store.selectedSupplyIds.length }}S · {{ store.selectedDemandIds.length }}D · {{ store.selectedNetworkIds.length }}N selected
    </div>
    <UButton
      block
      icon="i-heroicons-arrow-path"
      label="Reload from API"
      color="neutral"
      variant="outline"
      size="sm"
      :loading="referential.referentialLoading"
      @click="referential.loadReferential()"
    />
  </div>
</template>

<script setup lang="ts">
import { useSimulationStore } from '~/stores/simulation'
import { useReferentialStore } from '~/stores/referential'

const store = useSimulationStore()
const referential = useReferentialStore()
</script>
