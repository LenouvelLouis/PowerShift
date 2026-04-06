<template>
  <div class="relative overflow-hidden bg-[#0F172A] rounded-xl border border-[#1E293B] p-8">
    <div class="absolute inset-0 bg-gradient-to-r from-transparent via-[#334155]/30 to-transparent -translate-x-full animate-[shimmer_1.4s_infinite]" />
    <div class="relative">
      <div class="flex items-center gap-3 mb-6">
        <div class="h-8 w-8 rounded-full border-2 border-[#3C83F8]/60 border-t-[#7DD3FC] animate-spin" />
        <div>
          <p class="text-white font-semibold">
            {{ headline }}
          </p>
          <p class="text-sm text-gray-400">
            {{ subtitle }}
          </p>
        </div>
      </div>
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div
          v-for="i in 4"
          :key="`kpi-${i}`"
          class="bg-[#020617] p-5 rounded-xl border border-[#1E293B]"
        >
          <div class="h-3 w-20 rounded bg-slate-700/50 mb-3" />
          <div class="h-8 w-28 rounded bg-slate-700/40" />
        </div>
      </div>
      <div class="bg-[#020617] rounded-xl border border-[#1E293B] p-6">
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
}>()
</script>
