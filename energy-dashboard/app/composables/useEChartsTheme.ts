import type { ComposeOption } from 'echarts/core'
import type { LineSeriesOption, BarSeriesOption } from 'echarts/charts'
import type {
  GridComponentOption,
  TooltipComponentOption,
  LegendComponentOption,
  DataZoomComponentOption,
  TitleComponentOption
} from 'echarts/components'

export type ECOption = ComposeOption<
  | LineSeriesOption
  | BarSeriesOption
  | GridComponentOption
  | TooltipComponentOption
  | LegendComponentOption
  | DataZoomComponentOption
  | TitleComponentOption
>

const BG = '#0F172A'
const BORDER = '#1E293B'
const TEXT_DIM = '#64748B'
const TEXT_MID = '#94A3B8'
const TEXT_BRIGHT = '#E2E8F0'

export function useEChartsTheme() {
  const baseGrid = { left: 48, right: 16, top: 16, bottom: 48, containLabel: false }

  const baseTooltip: TooltipComponentOption = {
    backgroundColor: BG,
    borderColor: BORDER,
    borderWidth: 1,
    textStyle: { color: TEXT_MID, fontSize: 11 }
  }

  const baseLegend: LegendComponentOption = {
    bottom: 0,
    textStyle: { color: TEXT_MID, fontSize: 11 },
    icon: 'roundRect',
    itemWidth: 10,
    itemHeight: 10
  }

  const baseXAxis = {
    axisLine: { lineStyle: { color: BORDER } },
    axisTick: { lineStyle: { color: BORDER } },
    axisLabel: { color: TEXT_DIM, fontSize: 10 },
    splitLine: { lineStyle: { color: BORDER } }
  }

  const baseYAxis = {
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: TEXT_DIM, fontSize: 10 },
    splitLine: { lineStyle: { color: BORDER } }
  }

  function lineOption(opts: {
    labels: string[]
    series: { name: string; data: number[]; color: string }[]
    yTitle?: string
  }): ECOption {
    const useDataZoom = opts.labels.length > 48

    return {
      backgroundColor: 'transparent',
      grid: {
        ...baseGrid,
        bottom: useDataZoom ? 80 : 48
      },
      tooltip: {
        ...baseTooltip,
        trigger: 'axis'
      },
      legend: baseLegend,
      xAxis: {
        ...baseXAxis,
        type: 'category',
        data: opts.labels,
        axisLabel: {
          ...baseXAxis.axisLabel,
          interval: opts.labels.length > 48 ? Math.floor(opts.labels.length / 24) - 1 : 'auto'
        }
      },
      yAxis: {
        ...baseYAxis,
        type: 'value',
        name: opts.yTitle,
        nameTextStyle: { color: TEXT_DIM, fontSize: 11 },
        nameLocation: 'end'
      },
      dataZoom: useDataZoom
        ? [
            { type: 'slider', bottom: 40, height: 20, borderColor: BORDER, fillerColor: '#1E293B88', handleStyle: { color: TEXT_DIM }, textStyle: { color: TEXT_DIM, fontSize: 10 } },
            { type: 'inside' }
          ]
        : undefined,
      series: opts.series.map(s => ({
        name: s.name,
        type: 'line' as const,
        data: s.data,
        smooth: true,
        symbol: opts.labels.length > 48 ? 'none' : 'circle',
        symbolSize: 4,
        lineStyle: { color: s.color, width: 2 },
        itemStyle: { color: s.color },
        areaStyle: { color: s.color, opacity: 0.08 }
      }))
    }
  }

  function barOption(opts: {
    labels: string[]
    series: { name: string; data: number[]; colors?: string[]; color?: string }[]
    yTitle?: string
    yMax?: number
    stacked?: boolean
    showLegend?: boolean
    tooltipSuffix?: string
  }): ECOption {
    return {
      backgroundColor: 'transparent',
      grid: {
        ...baseGrid,
        bottom: opts.showLegend ? 48 : 32
      },
      tooltip: {
        ...baseTooltip,
        trigger: 'axis',
        formatter: opts.tooltipSuffix
          ? (params: any) => {
              const lines = (Array.isArray(params) ? params : [params]).map(
                (p: any) => `<span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${p.color};margin-right:4px"></span>${p.seriesName}: ${Number(p.value).toFixed(2)}${opts.tooltipSuffix}`
              )
              const title = Array.isArray(params) ? (params[0]?.name ?? '') : (params as any).name
              return `<div style="font-size:11px">${title}<br/>${lines.join('<br/>')}</div>`
            }
          : undefined
      },
      legend: opts.showLegend ? baseLegend : { show: false },
      xAxis: {
        ...baseXAxis,
        type: 'category',
        data: opts.labels
      },
      yAxis: {
        ...baseYAxis,
        type: 'value',
        name: opts.yTitle,
        nameTextStyle: { color: TEXT_DIM, fontSize: 11 },
        nameLocation: 'end',
        max: opts.yMax
      },
      series: opts.series.map(s => ({
        name: s.name,
        type: 'bar' as const,
        data: s.colors
          ? s.data.map((v, i) => ({ value: v, itemStyle: { color: s.colors![i], borderRadius: [4, 4, 0, 0] } }))
          : s.data,
        stack: opts.stacked ? 'total' : undefined,
        itemStyle: { borderRadius: [4, 4, 0, 0], ...(s.color ? { color: s.color } : {}) },
        barMaxWidth: 48
      }))
    }
  }

  return { lineOption, barOption }
}
