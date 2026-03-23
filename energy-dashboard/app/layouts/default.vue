<script setup>


//--------------SIDEBAR------------
const sidebarOpen = ref(true)
const tabGroups = [
  {
    label: 'Supply',
    tabs: [
      { id: 'wind_turbine', emoji: '💨', label: 'Wind Turbine',
        params: { name: '', type: 'wind_turbine', capacity_mw: 500, efficiency: 0.42, status: 'active', unit: 'MW', description: '' }
      },
      { id: 'solar_panel', emoji: '☀️', label: 'Solar Panel',
        params: { name: '', type: 'solar_panel', capacity_mw: 200, efficiency: 0.20, status: 'active', unit: 'MW', description: '' }
      },
      { id: 'nuclear_plant', emoji: '☢️', label: 'Nuclear Plant',
        params: { name: '', type: 'nuclear_plant', capacity_mw: 1000, efficiency: 0.95, status: 'active', unit: 'MW', description: '' }
      },
    ]
  },
  {
    label: 'Network',
    tabs: [
      { id: 'transformer', emoji: '🔌', label: 'Transformer',
        params: { name: '', type: 'transformer', voltage_kv: 400, voltage_hv_kv: 400, voltage_lv_kv: 20, capacity_mva: 500, status: 'active', unit: 'MVA', description: '' }
      },
      { id: 'cable', emoji: '🔌', label: 'Cable',
        params: { name: '', type: 'cable', voltage_kv: 20, length_km: 10, resistance_ohm_per_km: 0.1, reactance_ohm_per_km: 0.05, status: 'active', unit: 'MVA', description: '' }
      },
    ]
  },
  {
    label: 'Demand',
    tabs: [
      { id: 'house', emoji: '🏠', label: 'House',
        params: { name: '', type: 'house', load_mw: 120, status: 'active', unit: 'MW', description: '' }
      },
      { id: 'electric_vehicle', emoji: '🚗', label: 'E-Vehicle',
        params: { name: '', type: 'electric_vehicle', load_mw: 50, status: 'active', unit: 'MW', description: '' }
      },
    ]
  },
]
const activeGroup = ref('Supply')
const activeTab   = ref('Nuclear')
const allTabs     = computed(() => tabGroups.flatMap(g => g.tabs)) //tous les sous onglets
const currentTabs = computed(() => tabGroups.find(g => g.label === activeGroup.value)?.tabs ?? []) //liste des sous-onglets de l'onglet séléctionné
const selectedTab = computed(() => currentTabs.value.find(tab => tab.id === activeTab.value)) //Sous onglet sélectionné 
const tabOptions = computed(() => currentTabs.value.map(tab => ({label: tab.emoji + ' ' + tab.label, value: tab.id})))
watch(activeGroup, () => {activeTab.value = currentTabs.value[0]?.id ?? null})



//--------------SIMULATION------------





</script>



<template>
  <div class="flex flex-col h-screen bg-[#020617] text-white">

    <!-- Header -->
    <header class="bg-[#0F172A] flex items-center justify-between px-4 gap-2 h-14 border-b border-gray-200 dark:border-gray-800 shrink-0">
      
        <UButton
          variant="ghost" :icon="sidebarOpen ? 'i-heroicons-bars-3' : 'i-heroicons-bars-3'" 
          @click="sidebarOpen = !sidebarOpen"
        />
        <img src="/logo.png" alt="EnergyDash" class="h-10 w-auto" >
        <span class="font-bold text-lg  mr-50"> Energy Network Simulator 2026</span>
        
        <!--Bouton play stop -->
        <UButton icon="i-heroicons-play" color="success" label="Play"
/>
        <UButton icon="i-heroicons-stop" color="error" label="Stop" class="hover:bg-[#2d3f55] text-white" size="sm"/>
        <UButton icon="i-heroicons-arrow-down-tray" label="Exporter" class="bg-[#1E293B] hover:bg-[#2d3f55] text-white ml-auto" />
    
    </header>

    <div class="flex flex-1 overflow-hidden">

      <!-- Sidebar rétractable -->
      <Transition name="sidebar">
        <aside
          v-if="sidebarOpen"
          class="bg-[#0F172A] w-60 border-r border-gray-200 dark:border-gray-800 flex flex-col shrink-0 overflow-hidden"
        >
        <div class="w-56 flex flex-col bg-[#0F172A] h-full">

            <!-- Header avec les 3 catégories -->
            <div class="flex flex-row border-b border-[#1E293B]">
                <button
                v-for="group in tabGroups"
                :key="group.label"
                @click="activeGroup = group.label"
                class="flex-1 flex items-center justify-center gap-1 py-2 text-xs font-bold uppercase tracking-wider transition-all duration-200 cursor-pointer"
                :class="activeGroup === group.label
                    ? 'text-white border-b-2 border-[#3C83F8]'
                    : 'text-gray-500 hover:text-gray-300'"
                >
                <span>{{ group.tabs[0].emoji }}</span>
                <span>{{ group.label }}</span>
                </button>
            </div>

            <!-- Contenu — onglets du groupe actif -->
              <div class="flex-1 p-2 overflow-y-auto">
                <USelect
                  v-model="activeTab"
                  :items="tabOptions"
                  placeholder="Sélectionner..."
                  class="w-full"
                />
                <div class="flex-1 overflow-y-auto p-6">
                  <div v-if="selectedTab">

                    <!-- Boucle sur tous les params -->
                    <div v-for="(value, key) in selectedTab.params" :key="key">
                      <label>{{ key }}</label>
                      <UInput v-model="selectedTab.params[key]" />
                    </div>
                  </div>
                </div>
            </div>

             <div class="border-t border-[#1E293B] p-3 flex flex-col gap-2">
                <UButton
                block
                icon="i-heroicons-folder-open"
                label="Charger scénario"
                color="neutral"
                variant="outline"
                size="sm"
                />
                <UButton
                block
                icon="i-heroicons-cloud-arrow-up"
                label="Sauvegarder"
                color="primary"
                variant="solid"
                size="sm"
                />
            </div>
        </div>
        </aside>
      </Transition>

      <!-- Zone centrale -->
      <main class="flex-1 overflow-y-auto p-6">
        <NuxtPage />
      </main>
    </div>
  </div>
</template>

<style scoped>

.sidebar-enter-active,
.sidebar-leave-active {
  transition: width 0.4s ease, opacity 0.2s ease;
  width: 240px;
}
.sidebar-enter-from,
.sidebar-leave-to {
  width: 0;
  opacity: 0;
}
</style>
