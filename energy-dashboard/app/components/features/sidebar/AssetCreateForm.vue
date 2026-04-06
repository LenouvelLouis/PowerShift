<template>
  <div>
    <div class="flex items-center justify-between mt-2 mb-1">
      <p class="text-xs font-semibold text-[#3C83F8] uppercase tracking-wider">
        {{ config.title }}
      </p>
      <button
        class="text-xs text-gray-500 hover:text-gray-300"
        @click="$emit('cancel')"
      >
        ✕ Cancel
      </button>
    </div>
    <div class="space-y-2">
      <div>
        <label class="text-xs text-gray-400 block mb-0.5">Type</label>
        <USelect
          :model-value="form.type as string"
          :items="config.typeOptions"
          size="sm"
          class="w-full"
          @update:model-value="form.type = $event"
        />
      </div>
      <div>
        <label class="text-xs text-gray-400 block mb-0.5">Name</label>
        <UInput
          :model-value="form.name as string"
          size="sm"
          :placeholder="config.namePlaceholder ?? 'Name'"
          @update:model-value="form.name = $event"
        />
      </div>
      <div
        v-for="field in config.fields"
        :key="field.key"
      >
        <label class="text-xs text-gray-400 block mb-0.5">{{ field.label }}</label>
        <UInput
          :model-value="form[field.key] as number"
          type="number"
          :step="field.step"
          size="sm"
          @update:model-value="form[field.key] = $event"
        />
      </div>
    </div>
    <UButton
      block
      icon="i-heroicons-plus"
      label="Create and add"
      color="primary"
      size="sm"
      class="mt-3"
      :loading="loading"
      :disabled="loading || disabled"
      @click="$emit('submit', { ...form })"
    />
  </div>
</template>

<script setup lang="ts">
export interface CreateFormField {
  key: string
  label: string
  step?: number
}

export interface CreateFormConfig {
  title: string
  namePlaceholder?: string
  typeOptions: Array<{ label: string, value: string }>
  fields: CreateFormField[]
  defaults: Record<string, unknown>
}

const props = defineProps<{
  config: CreateFormConfig
  loading: boolean
  disabled: boolean
}>()

defineEmits<{
  submit: [form: Record<string, unknown>]
  cancel: []
}>()

const form = reactive<Record<string, unknown>>({ ...props.config.defaults })

watch(() => props.config, (cfg) => {
  Object.assign(form, { ...cfg.defaults })
}, { deep: true })

// Reset name after parent signals success (parent resets via key or watches submit)
defineExpose({
  resetName: () => { form.name = '' }
})
</script>
