/**
 * Generates time labels for chart X axis from a given number of hourly data points.
 * - If startDate is provided, labels are real dates: "Jan 01", "02:00", etc.
 *   Midnight ticks show the date ("Jan 02"), other ticks show the hour ("06:00").
 * - If no startDate, falls back to "H0", "H1", ...
 */
export function useTimeLabels(startDate: string | null | undefined | (() => string | null | undefined)) {
  function getStartDate() {
    return typeof startDate === 'function' ? startDate() : startDate
  }

  function buildLabels(n: number): string[] {
    const sd = getStartDate()
    if (!sd) {
      return Array.from({ length: n }, (_, i) => `H${i}`)
    }
    const base = new Date(`${sd}T00:00:00`)
    return Array.from({ length: n }, (_, i) => {
      const d = new Date(base.getTime() + i * 3600_000)
      return d.toISOString()
    })
  }

  function axisLabelFormatter(value: string): string {
    if (value.startsWith('H')) return value
    const d = new Date(value)
    const h = d.getUTCHours()
    const min = d.getUTCMinutes()
    if (h === 0 && min === 0) {
      // Midnight: show short date "Jan 02"
      return d.toLocaleDateString('en-US', { month: 'short', day: '2-digit', timeZone: 'UTC' })
    }
    return `${String(h).padStart(2, '0')}:00`
  }

  function tooltipLabelFormatter(value: string): string {
    if (value.startsWith('H')) return value
    const d = new Date(value)
    return d.toLocaleDateString('en-US', {
      month: 'short', day: '2-digit', timeZone: 'UTC'
    }) + ' ' + String(d.getUTCHours()).padStart(2, '0') + ':00'
  }

  return { buildLabels, axisLabelFormatter, tooltipLabelFormatter }
}
