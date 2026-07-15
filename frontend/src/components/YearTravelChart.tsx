import type { CSSProperties } from 'react'

export interface YearChartEntry {
  year: number
  value: number
  valueLabel: string
  detail?: string
}

interface YearTravelChartProps {
  entries: YearChartEntry[] | undefined
  selectedYear: number | 'all' | null
  metricLabel: string
  onSelectYear: (year: number | 'all') => void
}

export function YearTravelChart({
  entries,
  selectedYear,
  metricLabel,
  onSelectYear,
}: YearTravelChartProps) {
  if (!entries?.length) return null

  const maxValue = Math.max(...entries.map((entry) => entry.value), 1)

  return (
    <section className="year-chart" aria-label={`World Cup ${metricLabel} by year`}>
      <div className="year-chart__header">
        <div>
          <span>{metricLabel} per World Cup</span>
          <button
            type="button"
            className={`year-chart__all ${selectedYear === 'all' ? 'year-chart__all--selected' : ''}`}
            onClick={() => onSelectYear('all')}
            aria-pressed={selectedYear === 'all'}
          >
            All years
          </button>
        </div>
        <span className="year-chart__hint">Click a bar to load the map</span>
      </div>
      <div className="year-chart__bars">
        {entries.map((entry) => {
          const isSelected = entry.year === selectedYear
          const heightPct = entry.value > 0 ? Math.max(8, (entry.value / maxValue) * 100) : 0
          const label = String(entry.year)

          return (
            <button
              key={entry.year}
              type="button"
              className={`year-chart__bar ${isSelected ? 'year-chart__bar--selected' : ''}`}
              style={{ '--bar-height': `${heightPct}%` } as CSSProperties}
              onClick={() => onSelectYear(entry.year)}
              aria-pressed={isSelected}
              aria-label={`${label}: ${entry.valueLabel}`}
              title={`${label}: ${entry.valueLabel}${entry.detail ? ` · ${entry.detail}` : ''}`}
            >
              <span className="year-chart__column" />
              <span className="year-chart__label">{label}</span>
            </button>
          )
        })}
      </div>
    </section>
  )
}
