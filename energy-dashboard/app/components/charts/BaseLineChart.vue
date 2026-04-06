<template>
  <div :class="height ?? 'h-72'">
    <Line
      :data="data"
      :options="options"
    />
  </div>
</template>

<script setup lang="ts">
import { Line } from 'vue-chartjs'
import type { ChartData, ChartOptions } from 'chart.js'

const props = defineProps<{
  data: ChartData<'line'>
  options: ChartOptions<'line'>
  height?: string
}>()

const { registerChartJs } = useChartTheme()
registerChartJs()

const options = computed(() => props.options)
</script>
