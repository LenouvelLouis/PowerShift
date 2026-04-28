<template>
  <UModal
    :open="open"
    @update:open="$emit('update:open', $event)"
  >
    <template #header>
      <h3 class="font-semibold text-white">
        Compare Scenarios
      </h3>
    </template>
    <template #body>
      <div class="flex flex-col gap-4">
        <div>
          <label class="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Scenario A</label>
          <USelectMenu
            v-model="selectedA"
            :items="options"
            value-key="value"
            placeholder="Select first scenario..."
          >
            <template #item="{ item }">
              <span class="truncate">{{ item.label }}</span>
            </template>
          </USelectMenu>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Scenario B</label>
          <USelectMenu
            v-model="selectedB"
            :items="options"
            value-key="value"
            placeholder="Select second scenario..."
          >
            <template #item="{ item }">
              <span class="truncate">{{ item.label }}</span>
            </template>
          </USelectMenu>
        </div>
        <p
          v-if="errorMsg"
          class="text-xs text-red-400"
        >
          {{ errorMsg }}
        </p>
      </div>
    </template>
    <template #footer>
      <div class="flex justify-end gap-2">
        <UButton
          label="Cancel"
          color="neutral"
          variant="ghost"
          @click="$emit('update:open', false)"
        />
        <UButton
          label="Compare"
          color="primary"
          :loading="fetching"
          :disabled="!canCompare"
          @click="doCompare"
        />
      </div>
    </template>
  </UModal>
</template>

<script setup lang="ts">
import { fetchSimulationById, type SimulationResult, type SimulationListItem } from '~/composables/api'
import { useHistoryStore } from '~/stores/history'

const props = defineProps<{ open: boolean }>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  'compare': [a: SimulationResult, b: SimulationResult]
}>()

const history = useHistoryStore()

const selectedA = ref('')
const selectedB = ref('')
const fetching = ref(false)
const errorMsg = ref('')

const options = computed(() =>
  (history.simulationHistory as SimulationListItem[]).map((s, i) => ({
    label: s.name
      ? `${s.name} - ${s.status} - ${s.solver.toUpperCase()}`
      : `#${i + 1} - ${s.status} - ${s.solver.toUpperCase()}`,
    value: s.id
  }))
)

const canCompare = computed(() =>
  selectedA.value && selectedB.value && selectedA.value !== selectedB.value && !fetching.value
)

watch(() => props.open, (v) => {
  if (v) {
    errorMsg.value = ''
    selectedA.value = ''
    selectedB.value = ''
  }
})

async function doCompare() {
  if (!canCompare.value) return
  fetching.value = true
  errorMsg.value = ''
  try {
    const [a, b] = await Promise.all([
      fetchSimulationById(selectedA.value),
      fetchSimulationById(selectedB.value)
    ])
    emit('compare', a, b)
    emit('update:open', false)
  } catch {
    errorMsg.value = 'Failed to fetch simulation data. Please try again.'
  } finally {
    fetching.value = false
  }
}
</script>
