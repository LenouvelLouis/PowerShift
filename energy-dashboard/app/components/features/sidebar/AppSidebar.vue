<template>
  <aside class="w-60 bg-white dark:bg-slate-900 border-r border-gray-200 dark:border-slate-800 flex flex-col shrink-0 overflow-hidden">
    <div class="flex-1 overflow-y-auto">
      <SidebarAssetSection
        v-for="section in sections"
        :key="section.config.group"
        :config="section.config"
        :active="activeGroup === section.config.group"
        :selected-ids="section.selectedIds.value"
        :selected-assets="section.selectedAssets.value"
        :available-for-dropdown="section.availableForDropdown.value"
        @toggle="setActiveGroup(section.config.group)"
        @add-asset="handleAdd(section.config.storeType, $event)"
        @remove-asset="handleRemove(section.config.storeType, $event)"
        @delete-asset="$emit('delete-asset', $event)"
        @create-asset="handleCreate"
      />

      <div
        v-if="referential.referentialLoading"
        class="flex justify-center py-4"
      >
        <div class="animate-spin h-5 w-5 border-t-2 border-blue-500 rounded-full" />
      </div>
    </div>

    <SidebarFooter />
  </aside>
</template>

<script setup lang="ts">
import { useSimulationStore } from '~/stores/simulation'
import { useReferentialStore } from '~/stores/referential'
import type { Supply, Demand, NetworkComponent } from '~/composables/api'
import type { AssetSectionConfig } from './AssetSection.vue'

const _emit = defineEmits<{
  'delete-asset': [target: { id: string, name: string, group: string }]
}>()

const store = useSimulationStore()
const referential = useReferentialStore()
const toast = useToast()

const activeGroup = ref<'Supply' | 'Demand' | 'Storage' | 'Network'>('Supply')

function setActiveGroup(group: 'Supply' | 'Demand' | 'Storage' | 'Network') {
  activeGroup.value = group
}

// ─── Section definitions ────────────────────────────────────────────────────

const supplyConfig: AssetSectionConfig = {
  group: 'Supply',
  storeType: 'supply',
  icon: 'i-heroicons-bolt',
  iconColor: 'text-amber-400',
  emptyLabel: 'No supply selected',
  createFormConfig: {
    title: 'New Supply asset',
    namePlaceholder: 'e.g. Wind Farm Alpha',
    typeOptions: [
      { label: 'Wind Turbine', value: 'wind_turbine' },
      { label: 'Solar Panel', value: 'solar_panel' },
      { label: 'Nuclear Plant', value: 'nuclear_plant' }
    ],
    fields: [
      { key: 'capacity_mw', label: 'Capacity (MW)', tooltip: 'Installed power capacity in MW. Wind/solar are further scaled by a KNMI weather profile (0–1).' },
      { key: 'efficiency', label: 'Efficiency (0–1)', step: 0.01, tooltip: 'For nuclear plants: thermal-to-electric conversion efficiency. Wind and solar efficiency is embedded in the weather profile.' }
    ],
    defaults: { type: 'wind_turbine', name: '', capacity_mw: 500, efficiency: 0.42, status: 'active', unit: 'MW', description: '' }
  }
}

const storageConfig: AssetSectionConfig = {
  group: 'Storage',
  storeType: 'supply',
  icon: 'i-heroicons-battery-100',
  iconColor: 'text-green-400',
  emptyLabel: 'No storage selected',
  createFormConfig: {
    title: 'New Battery Storage',
    namePlaceholder: 'e.g. Grid Battery 100 MW',
    typeOptions: [
      { label: 'Battery Storage', value: 'battery_storage' }
    ],
    fields: [
      { key: 'capacity_mw', label: 'Power (MW)', tooltip: 'Max charge/discharge rate in MW.' },
      { key: 'efficiency', label: 'Efficiency (0–1)', step: 0.01, tooltip: 'One-way efficiency (e.g. 0.95 → round-trip ~90%). Li-ion typically 0.92–0.95.' }
    ],
    defaults: { type: 'battery_storage', name: '', capacity_mw: 200, efficiency: 0.95, status: 'active', unit: 'MW', description: '' }
  }
}

const demandConfig: AssetSectionConfig = {
  group: 'Demand',
  storeType: 'demand',
  icon: 'i-heroicons-home',
  iconColor: 'text-emerald-400',
  emptyLabel: 'No demand selected',
  createFormConfig: {
    title: 'New Demand asset',
    namePlaceholder: 'e.g. Groningen Zone A',
    typeOptions: [
      { label: 'House', value: 'house' },
      { label: 'Electric Vehicle', value: 'electric_vehicle' }
    ],
    fields: [
      { key: 'load_mw', label: 'Load (MW)', tooltip: 'Peak consumption in MW for this demand node. PyPSA multiplies this by a normalised hourly load profile (0–1), so actual demand varies hour by hour.' }
    ],
    defaults: { type: 'house', name: '', load_mw: 120, status: 'active', unit: 'MW', description: '' }
  }
}

const networkConfig: AssetSectionConfig = {
  group: 'Network',
  storeType: 'network',
  icon: 'i-heroicons-share',
  iconColor: 'text-blue-400',
  emptyLabel: 'No network component selected',
  createFormConfig: {
    title: 'New Network asset',
    namePlaceholder: 'e.g. HV Transformer 01',
    typeOptions: [
      { label: 'Transformer', value: 'transformer' },
      { label: 'Cable', value: 'cable' }
    ],
    fields: [
      { key: 'voltage_kv', label: 'Voltage (kV)', tooltip: 'Nominal voltage level of this network component. All assets connect to a single 380 kV bus in the LOPF model — this value is informational and shown in the Network canvas.' },
      { key: 'capacity_mva', label: 'Capacity (MVA)', tooltip: 'Apparent power rating in MVA. PyPSA checks this against actual power flow to compute the line loading % shown in the Network tab. Above 100% = overloaded.' }
    ],
    defaults: { type: 'transformer', name: '', voltage_kv: 400, capacity_mva: 500, status: 'active', unit: 'MVA', description: '' }
  }
}

const sections = [
  {
    config: supplyConfig,
    selectedIds: computed(() =>
      store.selectedSupplies.filter((s: Supply) => s.type !== 'battery_storage').map((s: Supply) => s.id)
    ),
    selectedAssets: computed(() =>
      store.selectedSupplies.filter((s: Supply) => s.type !== 'battery_storage') as Array<Supply | Demand | NetworkComponent>
    ),
    availableForDropdown: computed(() =>
      referential.availableSupplies
        .filter((s: Supply) => s.type !== 'battery_storage')
        .filter((s: Supply) => !store.selectedSupplyIds.includes(s.id))
        .map((s: Supply) => ({ label: s.name, value: s.id, name: s.name }))
    )
  },
  {
    config: demandConfig,
    selectedIds: computed(() => store.selectedDemandIds),
    selectedAssets: computed(() => store.selectedDemands as Array<Supply | Demand | NetworkComponent>),
    availableForDropdown: computed(() =>
      referential.availableDemands
        .filter((d: Demand) => !store.selectedDemandIds.includes(d.id))
        .map((d: Demand) => ({ label: d.name, value: d.id, name: d.name }))
    )
  },
  {
    config: storageConfig,
    selectedIds: computed(() =>
      store.selectedSupplies.filter((s: Supply) => s.type === 'battery_storage').map((s: Supply) => s.id)
    ),
    selectedAssets: computed(() =>
      store.selectedSupplies.filter((s: Supply) => s.type === 'battery_storage') as Array<Supply | Demand | NetworkComponent>
    ),
    availableForDropdown: computed(() =>
      referential.availableSupplies
        .filter((s: Supply) => s.type === 'battery_storage')
        .filter((s: Supply) => !store.selectedSupplyIds.includes(s.id))
        .map((s: Supply) => ({ label: s.name, value: s.id, name: s.name }))
    )
  },
  {
    config: networkConfig,
    selectedIds: computed(() => store.selectedNetworkIds),
    selectedAssets: computed(() => store.selectedNetwork as Array<Supply | Demand | NetworkComponent>),
    availableForDropdown: computed(() =>
      referential.availableNetwork
        .filter((n: NetworkComponent) => !store.selectedNetworkIds.includes(n.id))
        .map((n: NetworkComponent) => ({ label: n.name, value: n.id, name: n.name }))
    )
  }
]

// ─── Actions ────────────────────────────────────────────────────────────────

function handleAdd(storeType: 'supply' | 'demand' | 'network', id: string) {
  if (storeType === 'supply') store.addSupplyToSelection(id)
  else if (storeType === 'demand') store.addDemandToSelection(id)
  else store.addNetworkToSelection(id)
}

function handleRemove(storeType: 'supply' | 'demand' | 'network', id: string) {
  if (storeType === 'supply') store.removeSupplyFromSelection(id)
  else if (storeType === 'demand') store.removeDemandFromSelection(id)
  else store.removeNetworkFromSelection(id)
}

async function handleCreate(group: string, form: Record<string, unknown>) {
  try {
    if (group === 'Supply') {
      const created = await referential.addSupply(form as Parameters<typeof referential.addSupply>[0])
      store.addSupplyToSelection(created.id)
    } else if (group === 'Demand') {
      const created = await referential.addDemand(form as Parameters<typeof referential.addDemand>[0])
      store.addDemandToSelection(created.id)
    } else {
      const created = await referential.addNetworkComponent({
        ...(form as Parameters<typeof referential.addNetworkComponent>[0]),
        losses_kw: null,
        voltage_hv_kv: null,
        voltage_lv_kv: null,
        length_km: null,
        resistance_ohm_per_km: null,
        reactance_ohm_per_km: null
      })
      store.addNetworkToSelection(created.id)
    }
    toast.add({ title: 'Asset created and added to simulation', color: 'success' })
  } catch (e: unknown) {
    toast.add({ title: 'Error', description: e instanceof Error ? e.message : 'Unknown error', color: 'error' })
  }
}
</script>
