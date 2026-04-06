<template>
  <UModal
    :open="open"
    @update:open="$emit('update:open', $event)"
  >
    <template #header>
      <h3 class="font-semibold text-white">
        Rename scenario
      </h3>
    </template>
    <template #body>
      <UInput
        v-model="draft"
        placeholder="Scenario name"
        autofocus
        @keyup.enter="confirm"
      />
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
          label="Rename"
          color="primary"
          :loading="loading"
          :disabled="!draft.trim()"
          @click="confirm"
        />
      </div>
    </template>
  </UModal>
</template>

<script setup lang="ts">
const props = defineProps<{
  open: boolean
  initialName: string
  loading: boolean
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  'confirm': [name: string]
}>()

const draft = ref(props.initialName)

watch(() => props.initialName, (val) => { draft.value = val })

function confirm() {
  if (!draft.value.trim()) return
  emit('confirm', draft.value.trim())
}
</script>
