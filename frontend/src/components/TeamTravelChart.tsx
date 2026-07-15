import type { CSSProperties } from 'react'
import { getTeamFlag } from '../utils/teamFlags'

export interface TeamChartEntry {
  teamId: string
  teamName: string
  value: number
  valueLabel: string
  detail?: string
}

interface TeamTravelChartProps {
  entries: TeamChartEntry[] | undefined
  selectedTeamId: string | null
  metricLabel: string
  onSelectTeam: (teamId: string | null) => void
}

export function TeamTravelChart({
  entries,
  selectedTeamId,
  metricLabel,
  onSelectTeam,
}: TeamTravelChartProps) {
  if (!entries?.length) return null

  const maxValue = Math.max(...entries.map((entry) => entry.value), 1)

  return (
    <section className="team-chart" aria-label={`Team ${metricLabel}`}>
      <div className="team-chart__header">
        <div>
          <span className="team-chart__title">Teams</span>
          <span className="team-chart__subtitle">{metricLabel}</span>
        </div>
        <button
          type="button"
          className={`team-chart__all ${selectedTeamId ? '' : 'team-chart__all--selected'}`}
          onClick={() => onSelectTeam(null)}
          aria-pressed={!selectedTeamId}
        >
          All
        </button>
      </div>
      <div className="team-chart__bars">
        {entries.map((entry) => {
          const isSelected = entry.teamId === selectedTeamId
          const widthPct = entry.value > 0 ? Math.max(4, (entry.value / maxValue) * 100) : 0
          const flag = getTeamFlag(entry.teamName, entry.teamId)

          return (
            <button
              key={entry.teamId}
              type="button"
              className={`team-chart__bar ${isSelected ? 'team-chart__bar--selected' : ''}`}
              style={{ '--bar-width': `${widthPct}%` } as CSSProperties}
              onClick={() => onSelectTeam(entry.teamId)}
              aria-pressed={isSelected}
              aria-label={`${entry.teamName}: ${entry.valueLabel}`}
              title={`${entry.teamName}: ${entry.valueLabel}${entry.detail ? ` · ${entry.detail}` : ''}`}
            >
              <span className="team-chart__team">
                <span
                  className={`team-chart__flag ${flag.isFallback ? 'team-chart__flag--fallback' : ''}`}
                  aria-label={flag.label}
                  title={flag.label}
                >
                  {flag.imageUrl && (
                    <img
                      src={flag.imageUrl}
                      alt=""
                      loading="lazy"
                      onError={(event) => {
                        event.currentTarget.hidden = true
                        event.currentTarget.nextElementSibling?.removeAttribute('hidden')
                      }}
                    />
                  )}
                  <span hidden={!!flag.imageUrl}>{flag.display}</span>
                </span>
                <span className="team-chart__name">{entry.teamName}</span>
              </span>
              <span className="team-chart__track">
                <span className="team-chart__fill" />
              </span>
              <span className="team-chart__value">{entry.valueLabel}</span>
            </button>
          )
        })}
      </div>
    </section>
  )
}
