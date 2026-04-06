<template>
  <UModal
    :open="open"
    @update:open="$emit('update:open', $event)"
  >
    <template #header>
      <h3 class="text-base font-semibold text-white">
        Save simulation
      </h3>
    </template>
    <template #body>
      <p class="text-sm text-gray-300">
        The parameters have changed since the last simulation was saved.
        Do you want to <span class="font-semibold text-white">replace</span> the existing simulation
        or save as a <span class="font-semibold text-white">new one</span>?
      </p>
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
          label="New simulation"
          color="neutral"
          variant="outline"
          :loading="loading"
          @click="$emit('new')"
        />
        <UButton
          label="Replace"
          color="primary"
          :loading="loading"
          @click="$emit('replace')"
        />
      </div>
    </template>
  </UModal>
</template>

<script setup lang="ts">
defineProps<{
  open: boolean
  loading: boolean
}>()

defineEmits<{
  'update:open': [value: boolean]
  'replace': []
  'new': []
}>()
</script>
