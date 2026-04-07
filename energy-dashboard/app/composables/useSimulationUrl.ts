import { useHistoryStore } from '~/stores/history'

export function useSimulationUrl() {
  const route = useRoute()
  const router = useRouter()
  const history = useHistoryStore()

  // Sync selectedSimulationId → URL
  watch(
    () => history.selectedSimulationId,
    (id) => {
      if (id) {
        router.replace({ query: { ...route.query, sim: id } })
      } else {
        const { sim: _removed, ...rest } = route.query
        router.replace({ query: rest })
      }
    },
  )

  // Restore simulation from URL on page load
  onMounted(async () => {
    const sim = route.query.sim
    if (typeof sim === 'string' && sim) {
      try {
        await history.loadSimulationById(sim)
      } catch {
        // Simulation not found — silently ignore
      }
    }
  })
}
