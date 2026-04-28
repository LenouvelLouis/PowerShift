import { fetchScenarioExport, type ScenarioExport } from '~/composables/api'
import { useSimulationStore } from '~/stores/simulation'
import { useHistoryStore } from '~/stores/history'

export function useScenarioIO() {
  const store = useSimulationStore()
  const history = useHistoryStore()
  const toast = useToast()

  const fileInputRef = ref<HTMLInputElement | null>(null)
  const dateMode = ref<'hours' | 'dates'>('hours')

  const todayMonthDay = new Date().toISOString().slice(5, 10)
  const DEFAULT_START = `2025-${todayMonthDay}`
  const DEFAULT_END = `2025-${todayMonthDay}`

  function setDateMode(mode: 'hours' | 'dates') {
    dateMode.value = mode
    if (mode === 'dates') {
      if (!store.startDate) store.startDate = DEFAULT_START
      if (!store.endDate) store.endDate = DEFAULT_END
    } else {
      store.startDate = ''
      store.endDate = ''
    }
  }

  function _getExportId(): string | null {
    return history.selectedSimulationId ?? history.currentResult?.id ?? null
  }

  async function handleExport() {
    const id = _getExportId()
    if (!id) return
    try {
      const scenario = await fetchScenarioExport(id)
      const name = history.currentResult?.name ?? id
      const filename = `scenario-${name}-${new Date().toISOString().slice(0, 10)}.json`
      const blob = new Blob([JSON.stringify(scenario, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      toast.add({ title: 'Export error', color: 'error' })
    }
  }

  function _downloadFromApi(id: string, format: 'csv' | 'pdf') {
    const a = document.createElement('a')
    a.href = `/api/v1/simulation/${id}/export/${format}`
    a.download = ''
    a.click()
  }

  function handleExportCsv() {
    const id = _getExportId()
    if (!id) return
    _downloadFromApi(id, 'csv')
  }

  function handleExportPdf() {
    const id = _getExportId()
    if (!id) return
    _downloadFromApi(id, 'pdf')
  }

  function handleImport(event: Event) {
    const file = (event.target as HTMLInputElement).files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const scenario = JSON.parse(e.target?.result as string) as ScenarioExport
        store.loadFromScenario(scenario, file.name.replace('.json', ''))
        dateMode.value = (scenario.start_date && scenario.end_date) ? 'dates' : 'hours'
        toast.add({ title: 'Scenario loaded', color: 'success' })
      } catch {
        toast.add({ title: 'Invalid file', color: 'error' })
      } finally {
        if (fileInputRef.value) fileInputRef.value.value = ''
      }
    }
    reader.readAsText(file)
  }

  return {
    fileInputRef,
    dateMode,
    setDateMode,
    handleExport,
    handleExportCsv,
    handleExportPdf,
    handleImport
  }
}
