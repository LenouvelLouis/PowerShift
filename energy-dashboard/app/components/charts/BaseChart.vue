<template>
  <div :class="height ?? 'h-72'">
    <VChart
      :option="option"
      :autoresize="true"
      class="w-full h-full"
    />
  </div>
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
}>()
</script>
