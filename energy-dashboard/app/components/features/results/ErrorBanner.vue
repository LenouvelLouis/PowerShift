<template>
  <div class="px-5 py-4 bg-red-900/20 border border-red-700/60 rounded-xl flex items-start gap-3">
    <span class="text-red-400 text-xl leading-none mt-0.5">✗</span>
    <div>
      <p class="font-semibold text-red-300">
        {{ headline }}
      </p>
      <p class="text-sm text-red-400/80 mt-1">
        {{ description }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  headline: string
  description: string
}>()
</script>
