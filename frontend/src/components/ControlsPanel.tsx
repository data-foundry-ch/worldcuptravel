import type { MetaResponse } from '../types/api'

interface ControlsPanelProps {
  meta: MetaResponse | undefined
  year: number | 'all' | null
  team: string | null
  error: string | null
  itineraryOpen: boolean
  onToggleItinerary: () => void
  onOpenMethodology: () => void
}

export function ControlsPanel({
  meta,
  year,
  team,
  error,
  itineraryOpen,
  onToggleItinerary,
  onOpenMethodology,
}: ControlsPanelProps) {
  return (
    <div className="controls">
      <header className="controls__brand">
        <h1>
          <span className="controls__title-icon" aria-hidden="true">
            ⚽
          </span>
          <span>World Cup Travel Atlas</span>
        </h1>
        <button type="button" className="btn btn--link" onClick={onOpenMethodology}>
          Methodology
        </button>
      </header>

      {error && <p className="controls__error">{error}</p>}

      <p className="controls__selected-year">
        {year === 'all' ? 'All World Cups' : `World Cup ${year ?? '—'}`}
      </p>
      <p className="controls__selected-team">
        {team ? 'Team route selected' : 'Showing all team movements'}
      </p>

      <div className="controls__actions">
        <button type="button" className="btn btn--ghost" onClick={onToggleItinerary}>
          {itineraryOpen ? 'Hide itinerary' : 'Show itinerary'}
        </button>
      </div>

      {meta && (
        <div className="freshness-badge" title="Data source freshness">
          <span>Source: OpenFootball ({meta.source_ref})</span>
          <span>
            Coverage: {meta.coordinate_coverage.coverage_pct}% ·{' '}
            {meta.last_successful_download_timestamp
              ? new Date(meta.last_successful_download_timestamp).toLocaleString()
              : 'Unknown'}
          </span>
        </div>
      )}
    </div>
  )
}
