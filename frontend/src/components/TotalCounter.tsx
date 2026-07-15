import { formatKm } from '../utils/haversine'

interface TotalCounterProps {
  totalKm: number
  completedKm: number
  projectedKm: number
  animatedKm?: number
  isProjectedRoute: boolean
}

export function TotalCounter({
  totalKm,
  completedKm,
  projectedKm,
  animatedKm,
  isProjectedRoute,
}: TotalCounterProps) {
  const display = animatedKm ?? totalKm
  return (
    <div className="total-counter" aria-live="polite">
      <span className="total-counter__label">Approximate match-location travel</span>
      <span className="total-counter__value">{formatKm(display)}</span>
      <span className="total-counter__unit">km</span>
      {isProjectedRoute && projectedKm > 0 && (
        <span className="total-counter__sub">
          {formatKm(completedKm)} completed + {formatKm(projectedKm)} projected
        </span>
      )}
    </div>
  )
}
