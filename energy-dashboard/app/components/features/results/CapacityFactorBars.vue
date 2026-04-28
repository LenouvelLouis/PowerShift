<template>
  <div class="bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 p-5">
    <h3 class="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
      {{ $t('results.capacityFactors') }}
    </h3>
    <div class="space-y-3">
      <div
        v-for="{ name, cf, color } in factors"
        :key="name"
      >
        <div class="flex items-center justify-between mb-1">
          <span
            class="text-xs text-gray-600 dark:text-gray-400 truncate mr-2 flex items-center gap-1"
            :title="name"
          >
            <UIcon
              :name="generatorIcon(name)"
              class="w-3 h-3 shrink-0"
            />
            {{ name }}
          </span>
          <span class="font-mono text-gray-900 dark:text-white text-xs shrink-0">{{ (cf * 100).toFixed(1) }}%</span>
        </div>
        <div class="w-full bg-gray-200 dark:bg-slate-800 rounded-full h-1.5">
          <div
            class="h-1.5 rounded-full transition-all duration-700"
            :style="{ width: `${Math.min(cf * 100, 100)}%`, backgroundColor: color }"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  factors: Array<{ name: string, cf: number, color: string }>
}>()
</script>
