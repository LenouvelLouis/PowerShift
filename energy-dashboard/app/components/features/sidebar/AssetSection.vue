<template>
  <div class="border-b border-slate-800">
    <!-- Section header -->
    <button
      class="w-full flex items-center gap-2 px-3 py-2.5 text-sm font-medium hover:bg-slate-800/60 transition-colors cursor-pointer"
      :class="active ? 'text-blue-500' : 'text-gray-300'"
      @click="$emit('toggle')"
    >
      <UIcon
        :name="config.icon"
        class="w-3.5 h-3.5 shrink-0"
        :class="config.iconColor"
      />
      <span class="uppercase tracking-wider text-xs font-bold flex-1 text-left">{{ config.group }}</span>
      <span
        v-if="selectedIds.length"
        class="text-xs px-1.5 py-0.5 rounded bg-slate-800 text-gray-300 font-mono leading-none"
      >{{ selectedIds.length }}</span>
      <UIcon
        :name="active ? 'i-heroicons-chevron-up' : 'i-heroicons-chevron-right'"
        class="w-3 h-3 text-gray-500 shrink-0"
      />
    </button>

    <!-- Section body -->
    <div
      v-if="active"
      class="px-3 pb-3 space-y-3"
    >
      <!-- Create form -->
      <SidebarAssetCreateForm
        v-if="showCreateForm"
        ref="createFormRef"
        :config="config.createFormConfig"
        :loading="isCreating"
        :disabled="!backendAvailable"
        @submit="handleCreate"
        @cancel="showCreateForm = false"
      />

      <!-- Select + list -->
      <template v-else>
        <div class="mt-2">
          <div class="flex items-center justify-between mb-1.5">
            <p class="text-xs text-gray-500 uppercase tracking-wider">
              Add to simulation
            </p>
            <button
              class="text-xs text-blue-500 hover:text-blue-300 font-medium"
              :disabled="!backendAvailable"
              @click="showCreateForm = true"
            >
              + New
            </button>
          </div>
          <USelectMenu
            v-model="assetToAdd"
            :items="availableForDropdown"
            value-attribute="value"
            searchable
            search-placeholder="Search assets..."
            placeholder="Select an asset..."
            class="w-full"
            :disabled="!backendAvailable || availableForDropdown.length === 0"
            @update:model-value="handleAdd"
          >
            <template #item="{ item }">
              <div class="flex items-center justify-between w-full gap-2">
                <span class="flex-1 truncate">{{ item.label }}</span>
                <button
                  class="text-gray-700 hover:text-gray-500 flex-shrink-0 rounded"
                  @click.stop.prevent="$emit('delete-asset', { id: item.value as string, name: (item as { name?: string }).name ?? item.label, group: config.group })"
                >
                  <UIcon
                    name="i-heroicons-trash"
                    class="w-3 h-3"
                  />
                </button>
              </div>
            </template>
          </USelectMenu>
          <p
            v-if="backendAvailable && availableForDropdown.length === 0 && selectedAssets.length > 0"
            class="text-xs text-gray-600 mt-1 text-center"
          >
            All assets are selected
          </p>
          <p
            v-else-if="backendAvailable && availableForDropdown.length === 0 && selectedAssets.length === 0"
            class="text-xs text-gray-600 mt-1 text-center"
          >
            No assets — create one with + New
          </p>
        </div>

        <div
          v-if="selectedAssets.length"
          class="border-t border-slate-800 pt-2 space-y-1.5"
        >
          <SidebarAssetListItem
            v-for="asset in selectedAssets"
            :key="asset.id"
            :asset="asset"
            :expanded="expandedAssetId === asset.id"
            :has-overrides="store.hasOverrides(config.storeType, asset.id)"
            :summary="assetSummary(asset)"
            @toggle-expand="toggleExpand(asset.id)"
            @remove="$emit('remove-asset', asset.id)"
          >
            <SidebarAssetOverridePanel
              :asset="asset"
              :group-type="config.storeType"
            />
          </SidebarAssetListItem>
        </div>
        <p
          v-else
          class="text-xs text-gray-600 text-center py-2"
        >
          {{ config.emptyLabel }}
        </p>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useSimulationStore } from '~/stores/simulation'
import { useReferentialStore } from '~/stores/referential'
import type { Supply, Demand, NetworkComponent } from '~/composables/api'
import type { CreateFormConfig } from './AssetCreateForm.vue'

export interface AssetSectionConfig {
  group: 'Supply' | 'Demand' | 'Storage' | 'Network'
  storeType: 'supply' | 'demand' | 'network'
  icon: string
  iconColor: string
  emptyLabel: string
  createFormConfig: CreateFormConfig
}

const props = defineProps<{
  config: AssetSectionConfig
  active: boolean
  selectedIds: string[]
  selectedAssets: Array<Supply | Demand | NetworkComponent>
  availableForDropdown: Array<{ label: string, value: string, name: string }>
}>()

const emit = defineEmits<{
  'toggle': []
  'add-asset': [id: string]
  'remove-asset': [id: string]
  'delete-asset': [target: { id: string, name: string, group: string }]
  'create-asset': [group: string, form: Record<string, unknown>]
}>()

const store = useSimulationStore()
const referential = useReferentialStore()
const backendAvailable = computed(() => referential.backendAvailable)

const showCreateForm = ref(false)
const assetToAdd = ref<{ label: string, value: string, name: string } | undefined>(undefined)
const expandedAssetId = ref<string | null>(null)
const isCreating = ref(false)
const createFormRef = ref<{ resetName: () => void } | null>(null)

watch(() => props.active, (active) => {
  if (!active) {
    assetToAdd.value = undefined
    showCreateForm.value = false
    expandedAssetId.value = null
  }
})

function toggleExpand(id: string) {
  expandedAssetId.value = expandedAssetId.value === id ? null : id
}

function handleAdd(val: { label: string, value: string, name: string } | undefined) {
  if (!val) return
  emit('add-asset', val.value)
  nextTick(() => {
    assetToAdd.value = undefined
  })
}

async function handleCreate(form: Record<string, unknown>) {
  isCreating.value = true
  try {
    await emit('create-asset', props.config.group, form)
    showCreateForm.value = false
    createFormRef.value?.resetName()
  } finally {
    isCreating.value = false
  }
}

function assetSummary(asset: Supply | Demand | NetworkComponent): string {
  if ('capacity_mw' in asset) return `${(asset as Supply).capacity_mw} MW · eff ${(asset as Supply).efficiency}`
  if ('load_mw' in asset) return `${(asset as Demand).load_mw} MW`
  if ('voltage_kv' in asset) return `${(asset as NetworkComponent).voltage_kv} kV · ${(asset as NetworkComponent).capacity_mva} MVA`
  return ''
}
</script>
