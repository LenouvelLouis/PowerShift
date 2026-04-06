<template>
  <div class="flex flex-col h-screen bg-[#020617] text-white">
    <UToaster />

    <!-- Delete asset confirmation modal (triggered from sidebar) -->
    <UiConfirmModal
      :open="!!deleteTarget"
      title="Delete asset"
      :message="deleteTarget ? `Are you sure you want to permanently delete ${deleteTarget.name}? This action cannot be undone.` : ''"
      confirm-label="Delete"
      confirm-color="error"
      :loading="isDeleting"
      @update:open="(v) => { if (!v) deleteTarget = null }"
      @confirm="handleDeleteAsset"
    />

    <AppHeader @toggle-sidebar="sidebarOpen = !sidebarOpen" />

    <div class="flex flex-1 overflow-hidden">
      <Transition name="sidebar">
        <SidebarAppSidebar
          v-if="sidebarOpen"
          @delete-asset="deleteTarget = $event"
        />
      </Transition>
      <main class="flex-1 overflow-y-auto pb-10">
        <NuxtPage />
      </main>
    </div>

    <KpiFooter />
  </div>
</template>

<script setup lang="ts">
import { useSimulationStore } from '~/stores/simulation'

const store = useSimulationStore()
const toast = useToast()

const sidebarOpen = ref(true)
const deleteTarget = ref<{ id: string, name: string, group: string } | null>(null)
const isDeleting = ref(false)

async function handleDeleteAsset() {
  if (!deleteTarget.value) return
  isDeleting.value = true
  try {
    const { id, group } = deleteTarget.value
    if (group === 'Supply') await store.removeSupply(id)
    else if (group === 'Demand') await store.removeDemand(id)
    else await store.removeNetworkComponent(id)
    toast.add({ title: 'Asset deleted', color: 'success' })
    deleteTarget.value = null
  } catch (e: unknown) {
    toast.add({ title: 'Deletion error', description: e instanceof Error ? e.message : 'Unknown error', color: 'error' })
  } finally {
    isDeleting.value = false
  }
}
</script>

<style scoped>
.sidebar-enter-active,
.sidebar-leave-active {
  transition: width 0.3s ease, opacity 0.2s ease;
  width: 240px;
}
.sidebar-enter-from,
.sidebar-leave-to {
  width: 0;
  opacity: 0;
}
</style>
