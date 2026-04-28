import { fetchSimulationSolvers, type SimulationSolverInfo } from '~/composables/api'
import { useSimulationStore } from '~/stores/simulation'
import { useReferentialStore } from '~/stores/referential'

export interface SolverOption {
  label: string
  value: string
  description: string
  speed: string
  license: string
  bestFor: string
}

export const SOLVER_OPTIONS: readonly SolverOption[] = [
  { label: 'HiGHS', value: 'highs', description: 'Open-source LP solver — fast and reliable (default). Used for LOPF optimisation across all snapshots simultaneously.', speed: 'Fast', license: 'Open-source', bestFor: 'Default choice — recommended for all LOPF simulations' },
  { label: 'GLPK', value: 'glpk', description: 'Open-source LP/MIP solver — slower alternative to HiGHS for LOPF optimisation.', speed: 'Slow', license: 'Open-source', bestFor: 'Compatibility checks' },
  { label: 'CBC', value: 'cbc', description: 'COIN-OR open-source MIP solver — handles unit commitment in future hybrid AC/OPF modes.', speed: 'Medium', license: 'Open-source', bestFor: 'Future mixed-integer OPF with unit commitment' },
  { label: 'SCIP', value: 'scip', description: 'Academic MIP/NLP solver — supports constrained and non-linear power flow formulations.', speed: 'Medium', license: 'Academic', bestFor: 'Research-grade constrained power flow problems' },
  { label: 'Gurobi', value: 'gurobi', description: 'Commercial LP/MIP solver — ultra-fast for large-scale OPF. Requires a valid license.', speed: 'Very fast', license: 'Commercial', bestFor: 'Large-scale OPF with strict performance targets' },
  { label: 'CPLEX', value: 'cplex', description: 'IBM commercial LP/MIP — enterprise-grade robustness for large OPF workloads. Requires a valid license.', speed: 'Very fast', license: 'Commercial', bestFor: 'Enterprise OPF on large utility-scale networks' },
  { label: 'Xpress', value: 'xpress', description: 'FICO commercial LP/MIP — high-performance large-scale OPF. Requires a valid license.', speed: 'Very fast', license: 'Commercial', bestFor: 'High-performance OPF on large transmission networks' }
] as const

export function useSolverAvailability() {
  const store = useSimulationStore()
  const referential = useReferentialStore()
  const toast = useToast()

  const solverAvailabilityLoading = ref(false)
  const solverAvailabilityByName = ref<Record<string, SimulationSolverInfo>>({})

  const solverSelectItems = computed(() =>
    SOLVER_OPTIONS.map(({ label, value }) => {
      const info = solverAvailabilityByName.value[value]
      const isUnavailable = info ? !info.available : false
      return { label: isUnavailable ? `${label} (unavailable)` : label, value, disabled: isUnavailable }
    })
  )

  const selectedSolverTitle = computed(() => {
    const selected = SOLVER_OPTIONS.find(o => o.value === store.solver)
    if (!selected) return 'Solver'
    const info = solverAvailabilityByName.value[selected.value]
    if (info && !info.available) return `${selected.label} - ${selected.description}. Unavailable: ${info.reason ?? 'not installed'}`
    return `${selected.label} - ${selected.description}`
  })

  const selectedSolverLabel = computed(() => {
    const selected = SOLVER_OPTIONS.find(o => o.value === store.solver)
    if (!selected) return 'Unknown'
    const info = solverAvailabilityByName.value[selected.value]
    return info && !info.available ? `${selected.label} (unavailable)` : selected.label
  })

  async function refreshSolverAvailability() {
    solverAvailabilityLoading.value = true
    try {
      const solvers = await fetchSimulationSolvers()
      solverAvailabilityByName.value = Object.fromEntries(solvers.map(s => [s.name, s]))
    } catch {
      solverAvailabilityByName.value = {}
    } finally {
      solverAvailabilityLoading.value = false
    }
  }

  function isSolverUnavailable(solverName: string): boolean {
    const info = solverAvailabilityByName.value[solverName]
    return info ? !info.available : false
  }

  function solverUnavailableReason(solverName: string): string {
    const info = solverAvailabilityByName.value[solverName]
    if (!info || info.available) return ''
    return info.reason ?? 'Solver not available on backend.'
  }

  // Auto-switch when current solver becomes unavailable
  watch(
    solverSelectItems,
    (items) => {
      const current = items.find(item => item.value === store.solver)
      if (current && !current.disabled) return
      const fallback = items.find(item => !item.disabled)
      if (!fallback || store.solver === fallback.value) return
      const previousSolver = store.solver
      store.solver = fallback.value
      toast.add({ title: 'Solver switched', description: `Solver '${previousSolver}' is unavailable. Switched to '${fallback.value}'.`, color: 'warning' })
    },
    { immediate: true }
  )

  // Fetch availability when backend becomes available
  watch(
    () => referential.backendAvailable,
    (available) => { if (available) void refreshSolverAvailability() },
    { immediate: true }
  )

  return {
    solverOptions: SOLVER_OPTIONS,
    solverSelectItems,
    solverAvailabilityLoading,
    selectedSolverLabel,
    selectedSolverTitle,
    isSolverUnavailable,
    solverUnavailableReason,
    refreshSolverAvailability
  }
}
