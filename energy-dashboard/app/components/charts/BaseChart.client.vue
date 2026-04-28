<template>
  <div
    :class="height ?? 'h-72'"
    class="relative group"
  >
    <VChart
      v-if="!isFullscreen"
      :option="option"
      :autoresize="true"
      class="w-full h-full"
    />
    <div
      v-else
      class="w-full h-full"
    />
    <button
      class="absolute top-2 right-2 p-1 rounded opacity-0 group-hover:opacity-100 transition-opacity bg-gray-200 hover:bg-gray-300 dark:bg-slate-800 dark:hover:bg-slate-700 text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white z-10"
      title="Fullscreen"
      @click="isFullscreen = true"
    >
      <UIcon
        name="i-heroicons-arrows-pointing-out"
        class="w-3.5 h-3.5"
      />
    </button>
  </div>

  <Teleport to="body">
    <div
      v-if="isFullscreen"
      class="fixed inset-0 z-[9999] bg-white dark:bg-slate-950 flex flex-col p-6"
    >
      <div class="flex items-center justify-between mb-4 shrink-0">
        <h2
          v-if="title"
          class="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider"
        >
          {{ title }}
        </h2>
        <div v-else />
        <button
          class="p-1.5 rounded bg-gray-200 hover:bg-gray-300 dark:bg-slate-800 dark:hover:bg-slate-700 text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
          title="Exit fullscreen"
          @click="isFullscreen = false"
        >
          <UIcon
            name="i-heroicons-arrows-pointing-in"
            class="w-4 h-4"
          />
        </button>
      </div>
      <VChart
        :option="option"
        :autoresize="true"
        class="w-full flex-1"
      />
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
  TitleComponent
} from 'echarts/components'
import type { ECOption } from '~/composables/useEChartsTheme'

use([CanvasRenderer, LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent, DataZoomComponent, TitleComponent])

defineProps<{
  option: ECOption
  height?: string
  title?: string
}>()

const isFullscreen = ref(false)

onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') isFullscreen.value = false
}
</script>
