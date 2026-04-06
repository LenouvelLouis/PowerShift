<template>
  <div :class="height ?? 'h-52'">
    <Bar
      :data="data"
      :options="options"
    />
  </div>
</template>

<script setup lang="ts">
import { Bar } from 'vue-chartjs'
import type { ChartData, ChartOptions } from 'chart.js'

const props = defineProps<{
  data: ChartData<'bar'>
  options: ChartOptions<'bar'>
  height?: string
}>()

const { registerChartJs } = useChartTheme()
registerChartJs()

const options = computed(() => props.options)
</script>
