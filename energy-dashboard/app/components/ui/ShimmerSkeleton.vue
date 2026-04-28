<template>
  <div class="relative overflow-hidden bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 p-8">
    <div class="absolute inset-0 bg-gradient-to-r from-transparent via-gray-300/30 dark:via-slate-700/30 to-transparent -translate-x-full animate-[shimmer_1.4s_infinite]" />
    <div class="relative">
      <div class="flex items-center gap-3 mb-6">
        <div class="h-8 w-8 rounded-full border-2 border-blue-500/60 border-t-sky-300 animate-spin" />
        <div>
          <p class="text-gray-900 dark:text-white font-semibold">
            {{ headline }}
          </p>
          <p class="text-sm text-gray-600 dark:text-gray-400">
            {{ subtitle }}
            <span
              v-if="badge"
              class="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-500/20 text-blue-300 tabular-nums"
            >
              {{ badge }}
            </span>
          </p>
        </div>
      </div>
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div
          v-for="i in 4"
          :key="`kpi-${i}`"
          class="bg-gray-50 dark:bg-slate-950 p-5 rounded-xl border border-gray-200 dark:border-slate-800"
        >
          <div class="h-3 w-20 rounded bg-slate-700/50 mb-3" />
          <div class="h-8 w-28 rounded bg-slate-700/40" />
        </div>
      </div>
      <div class="bg-gray-50 dark:bg-slate-950 rounded-xl border border-gray-200 dark:border-slate-800 p-6">
        <div class="h-5 w-48 rounded bg-slate-700/50 mb-4" />
        <div class="h-64 rounded-lg bg-slate-700/30" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  headline: string
  subtitle: string
  badge?: string
}>()
</script>
