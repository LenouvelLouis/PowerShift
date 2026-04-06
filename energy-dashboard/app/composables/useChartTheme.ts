import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  type ChartOptions
} from 'chart.js'

let _registered = false

export function useChartTheme() {
  function registerChartJs() {
    if (_registered) return
    ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend, Filler)
    _registered = true
  }

  const darkTooltip = {
    backgroundColor: '#0F172A',
    titleColor: '#E2E8F0',
    bodyColor: '#94A3B8',
    borderColor: '#1E293B',
    borderWidth: 1
  }

  const darkGridX = { color: '#1E293B' }
  const darkGridY = { color: '#1E293B' }
  const darkTickStyle = { color: '#64748B', font: { size: 10 } }

  function lineChartOptions(opts: { yTitle?: string, xMaxTicks?: number } = {}): ChartOptions<'line'> {
    return {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          labels: { color: '#94A3B8', font: { size: 11 }, padding: 12, boxWidth: 10 }
        },
        tooltip: darkTooltip
      },
      scales: {
        x: {
          ticks: { ...darkTickStyle, maxTicksLimit: opts.xMaxTicks ?? 24 },
          grid: darkGridX
        },
        y: {
          beginAtZero: true,
          ticks: darkTickStyle,
          grid: darkGridY,
          title: opts.yTitle ? { display: true, text: opts.yTitle, color: '#64748B', font: { size: 11 } } : undefined
        }
      }
    }
  }

  function barChartOptions(opts: {
    yTitle?: string
    yMax?: number
    stacked?: boolean
    showLegend?: boolean
    tooltipSuffix?: string
  } = {}): ChartOptions<'bar'> {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: opts.showLegend
          ? { display: true, labels: { color: '#94A3B8', font: { size: 10 }, padding: 10, boxWidth: 10 } }
          : { display: false },
        tooltip: {
          ...darkTooltip,
          callbacks: {
            label: (ctx: import('chart.js').TooltipItem<'bar'>) => {
              const suffix = opts.tooltipSuffix ?? ''
              const y = typeof ctx.parsed.y === 'number' ? ctx.parsed.y : 0
              if (opts.showLegend && ctx.dataset?.label) {
                return ` ${ctx.dataset.label}: ${y.toFixed(2)}${suffix}`
              }
              return ` ${y.toFixed(2)}${suffix}`
            }
          }
        }
      },
      scales: {
        x: {
          stacked: opts.stacked,
          ticks: darkTickStyle,
          grid: darkGridX
        },
        y: {
          stacked: opts.stacked,
          beginAtZero: true,
          ...(opts.yMax !== undefined ? { max: opts.yMax } : {}),
          ticks: {
            ...darkTickStyle,
            ...(opts.yMax === 100 ? { callback: (v: number | string) => `${v}%` } : {})
          },
          grid: darkGridY,
          title: opts.yTitle ? { display: true, text: opts.yTitle, color: '#64748B', font: { size: 11 } } : undefined
        }
      }
    }
  }

  return { registerChartJs, lineChartOptions, barChartOptions }
}
