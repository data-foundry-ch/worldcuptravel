interface DataQualityBannerProps {
  warnings: string[]
  isStale: boolean
  unresolvedCount: number
}

export function DataQualityBanner({ warnings, isStale, unresolvedCount }: DataQualityBannerProps) {
  if (!warnings.length && !isStale && unresolvedCount === 0) return null

  return (
    <div className="data-quality" role="status">
      {isStale && <p className="data-quality__item">Source data may be stale.</p>}
      {unresolvedCount > 0 && (
        <p className="data-quality__item">
          {unresolvedCount} match location(s) have unresolved coordinates and are excluded from
          totals.
        </p>
      )}
      {warnings.map((w) => (
        <p key={w} className="data-quality__item">
          {w}
        </p>
      ))}
    </div>
  )
}
