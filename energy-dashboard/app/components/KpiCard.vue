<template>
  <div
    :class="[
      'rounded-lg border p-4 shadow-sm',
      status === 'ok' ? 'border-emerald-400 bg-emerald-50' : 'border-amber-400 bg-amber-50'
    ]"
  >
    <p class="text-sm font-medium text-gray-600">{{ label }}</p>
    <p class="mt-1 text-2xl font-bold text-gray-900">{{ value }}</p>
  </div>
</template>

<script setup>
defineProps({
  label: {
    type: String,
    required: true
  },
  value: {
    type: String,
    required: true
  },
  status: {
    type: String,
    default: 'ok'  // 'ok', 'warning', 'error'
  }
})
</script>
