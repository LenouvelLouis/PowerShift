import { fetchScenarioExport } from '~/composables/api'
import { useHistoryStore } from '~/stores/history'
import { useSimulationStore } from '~/stores/simulation'

export function useSimulationUrl() {
  const route = useRoute()
  const router = useRouter()
  const history = useHistoryStore()
  const sim = useSimulationStore()

  watch(
    () => history.selectedSimulationId,
    (id) => {
      if (!id && !route.query.sim) return
      if (id) {
        router.replace({ query: { ...route.query, sim: id } })
      } else {
        const { sim: _removed, ...rest } = route.query
        router.replace({ query: rest })
      }
    }
  )

  onMounted(async () => {
    const simId = route.query.sim
    if (typeof simId !== 'string' || !simId) return
    sim.isLoadingScenario = true
    try {
      if (!history.simulationHistory.length) await history.loadHistory()
      const entry = history.simulationHistory.find((s: { id: string }) => s.id === simId)
      await history.loadSimulationById(simId)
      const exported = await fetchScenarioExport(simId)
      sim.loadFromScenario(exported, entry?.name ?? '')
      sim.setReference(simId, sim.buildPayload())
      sim.selectedHistoryId = simId
    } catch {
      // Simulation not found or load failed — silently ignore
    } finally {
      await nextTick()
      sim.isLoadingScenario = false
    }
  })
}
