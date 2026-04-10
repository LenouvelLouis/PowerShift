<template>
  <UModal
    :open="open"
    @update:open="$emit('update:open', $event)"
  >
    <template #header>
      <div class="flex items-center justify-between gap-3 w-full">
        <div>
          <h3 class="text-base font-semibold text-white">
            Solver helper
          </h3>
          <p class="text-xs text-gray-400 mt-0.5">
            The solver is used for LOPF (Linear Optimal Power Flow). HiGHS is recommended for all simulations.
          </p>
        </div>
        <span class="text-xs px-2 py-1 rounded bg-[#1E293B] text-slate-300">
          Selected: {{ selectedSolverLabel }}
        </span>
      </div>
    </template>
    <template #body>
      <div class="space-y-2 max-h-[60vh] overflow-y-auto pr-1">
        <div
          v-for="solver in solverOptions"
          :key="solver.value"
          class="rounded-lg border border-[#1E293B] bg-[#0B1220] p-3"
          :class="solver.value === store.solver ? 'ring-1 ring-[#3C83F8]/60' : ''"
        >
          <div class="flex items-center justify-between gap-3 mb-1">
            <p class="text-sm font-semibold text-white">
              {{ solver.label }}
            </p>
            <div class="flex items-center gap-1.5">
              <span
                v-if="isSolverUnavailable(solver.value)"
                class="text-[11px] px-1.5 py-0.5 rounded bg-red-900/30 text-red-300"
              >Unavailable</span>
              <span class="text-[11px] px-1.5 py-0.5 rounded bg-[#1E293B] text-slate-300">{{ solver.license }}</span>
              <span class="text-[11px] px-1.5 py-0.5 rounded bg-[#1E293B] text-slate-300">{{ solver.speed }}</span>
            </div>
          </div>
          <p class="text-xs text-slate-300">
            {{ solver.description }}
          </p>
          <p class="text-xs text-gray-400 mt-1.5">
            Best for: {{ solver.bestFor }}
          </p>
          <p
            v-if="isSolverUnavailable(solver.value)"
            class="text-xs text-red-300/90 mt-1"
          >
            {{ solverUnavailableReason(solver.value) }}
          </p>
        </div>
      </div>
    </template>
    <template #footer>
      <div class="flex justify-end gap-2">
        <UButton
          label="Close"
          color="neutral"
          variant="ghost"
          @click="$emit('update:open', false)"
        />
      </div>
    </template>
  </UModal>
</template>

<script setup lang="ts">
import { useSimulationStore } from '~/stores/simulation'

defineProps<{ open: boolean }>()
defineEmits<{ 'update:open': [value: boolean] }>()

const store = useSimulationStore()
const { solverOptions, selectedSolverLabel, isSolverUnavailable, solverUnavailableReason } = useSolverAvailability()
</script>
