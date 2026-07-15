import { formatKm } from '../utils/haversine'
import type { TravelKpiMetric, TravelKpis } from '../utils/travelKpis'

interface TravelKpiPanelProps {
  kpis: TravelKpis
  selectedMetric: TravelKpiMetric
  onSelectMetric: (metric: TravelKpiMetric) => void
}

function formatCount(count: number): string {
  return count.toLocaleString('en-US')
}

function movementLabel(count: number): string {
  return count === 1 ? 'movement' : 'movements'
}

function KpiIcon({ icon }: { icon: string }) {
  return <span className="kpi-card__icon" aria-hidden="true">{icon}</span>
}

function KpiLabel({ label }: { label: string }) {
  return (
    <span className="kpi-card__label">
      <span>{label}</span>
    </span>
  )
}

function cardClass(metric: TravelKpiMetric, selectedMetric: TravelKpiMetric, extraClass = ''): string {
  return [
    'kpi-card',
    extraClass,
    selectedMetric === metric ? 'kpi-card--selected' : '',
  ].filter(Boolean).join(' ')
}

export function TravelKpiPanel({
  kpis,
  selectedMetric,
  onSelectMetric,
}: TravelKpiPanelProps) {
  return (
    <section className="kpi-panel" aria-label="Travel KPIs">
      <div className="kpi-panel__header">
        <span className="kpi-panel__eyebrow">Travel KPIs</span>
        <span className="kpi-panel__context">{kpis.averageBasis}</span>
      </div>

      <div className="kpi-grid">
        <button
          type="button"
          className={cardClass('totalTravel', selectedMetric, 'kpi-card--primary')}
          onClick={() => onSelectMetric('totalTravel')}
          aria-pressed={selectedMetric === 'totalTravel'}
        >
          <KpiIcon icon="✈" />
          <span className="kpi-card__body">
            <KpiLabel label="Total distance" />
            <span className="kpi-card__value">{formatKm(kpis.totalKm)}</span>
            <span className="kpi-card__unit">km</span>
          </span>
        </button>

        <button
          type="button"
          className={cardClass('averageTravel', selectedMetric)}
          onClick={() => onSelectMetric('averageTravel')}
          aria-pressed={selectedMetric === 'averageTravel'}
        >
          <KpiIcon icon="Ø" />
          <span className="kpi-card__body">
            <KpiLabel label="Average" />
            <span className="kpi-card__value">
              {kpis.averageKm == null ? '—' : formatKm(kpis.averageKm)}
            </span>
            {kpis.averageKm != null && <span className="kpi-card__unit">km</span>}
            <span className="kpi-card__detail">{kpis.averageBasis}</span>
          </span>
        </button>

        <button
          type="button"
          className={cardClass('averageLeg', selectedMetric)}
          onClick={() => onSelectMetric('averageLeg')}
          aria-pressed={selectedMetric === 'averageLeg'}
        >
          <KpiIcon icon="↗" />
          <span className="kpi-card__body">
            <KpiLabel label="Avg per leg" />
            <span className="kpi-card__value">
              {kpis.averageLegKm == null ? '—' : formatKm(kpis.averageLegKm)}
            </span>
            {kpis.averageLegKm != null && <span className="kpi-card__unit">km</span>}
          </span>
        </button>

        <button
          type="button"
          className={cardClass('longestLeg', selectedMetric)}
          onClick={() => onSelectMetric('longestLeg')}
          aria-pressed={selectedMetric === 'longestLeg'}
        >
          <KpiIcon icon="⇢" />
          <span className="kpi-card__body">
            <KpiLabel label="Longest leg" />
            <span className="kpi-card__value">
              {kpis.longestSingleLeg?.distanceKm == null
                ? '—'
                : formatKm(kpis.longestSingleLeg.distanceKm)}
            </span>
            {kpis.longestSingleLeg?.distanceKm != null && <span className="kpi-card__unit">km</span>}
            {kpis.longestSingleLeg && (
              <span className="kpi-card__detail">{kpis.longestSingleLeg.label}</span>
            )}
          </span>
        </button>

        <button
          type="button"
          className={cardClass('locationCount', selectedMetric)}
          onClick={() => onSelectMetric('locationCount')}
          aria-pressed={selectedMetric === 'locationCount'}
        >
          <KpiIcon icon="⌖" />
          <span className="kpi-card__body">
            <KpiLabel label="Venues" />
            <span className="kpi-card__value">{formatCount(kpis.locationCount)}</span>
          </span>
        </button>

        <button
          type="button"
          className={cardClass('mostRepeatedRoute', selectedMetric)}
          onClick={() => onSelectMetric('mostRepeatedRoute')}
          aria-pressed={selectedMetric === 'mostRepeatedRoute'}
        >
          <KpiIcon icon="⇄" />
          <span className="kpi-card__body">
            <KpiLabel label="Top route" />
            <span className="kpi-card__value">
              {kpis.mostRepeatedRoute?.movementCount == null
                ? '—'
                : formatCount(kpis.mostRepeatedRoute.movementCount)}
            </span>
            {kpis.mostRepeatedRoute?.movementCount != null && (
              <span className="kpi-card__unit">
                {movementLabel(kpis.mostRepeatedRoute.movementCount)}
              </span>
            )}
            {kpis.mostRepeatedRoute && (
              <span className="kpi-card__detail">{kpis.mostRepeatedRoute.label}</span>
            )}
          </span>
        </button>
      </div>
    </section>
  )
}
