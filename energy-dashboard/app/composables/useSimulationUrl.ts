import { useHistoryStore } from '~/stores/history'

export function useSimulationUrl() {
  const route = useRoute()
  const router = useRouter()
  const history = useHistoryStore()

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
    },
  )

  onMounted(async () => {
    const sim = route.query.sim
    if (typeof sim === 'string' && sim) {
      try {
        await history.loadHistory()
        await history.loadSimulationById(sim)
      } catch {
        // Simulation not found — silently ignore
      }
    }
  })
}
