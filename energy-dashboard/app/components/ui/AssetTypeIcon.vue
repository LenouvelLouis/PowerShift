<template>
  <UIcon :name="iconName" :class="['shrink-0', sizeClass, colorClass]" />
</template>

<script setup lang="ts">
const props = defineProps<{
  type: string
  size?: 'xs' | 'sm' | 'md'
  noColor?: boolean
}>()

const iconMap: Record<string, string> = {
  wind_turbine: 'i-heroicons-arrow-path',
  solar_panel: 'i-heroicons-sun',
  nuclear_plant: 'i-heroicons-bolt',
  house: 'i-heroicons-home',
  electric_vehicle: 'i-heroicons-truck',
  cable: 'i-heroicons-link',
  transformer: 'i-heroicons-cpu-chip',
}

const colorMap: Record<string, string> = {
  wind_turbine: 'text-sky-400',
  solar_panel: 'text-amber-400',
  nuclear_plant: 'text-purple-400',
  house: 'text-blue-400',
  electric_vehicle: 'text-emerald-400',
  cable: 'text-gray-400',
  transformer: 'text-orange-400',
}

const sizeMap = { xs: 'w-3 h-3', sm: 'w-3.5 h-3.5', md: 'w-4 h-4' }

const iconName = computed(() => iconMap[props.type] ?? 'i-heroicons-question-mark-circle')
const colorClass = computed(() => props.noColor ? '' : (colorMap[props.type] ?? 'text-gray-400'))
const sizeClass = computed(() => sizeMap[props.size ?? 'sm'])
</script>
