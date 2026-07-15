interface MethodologyDrawerProps {
  open: boolean
  onClose: () => void
  metricDefinition: string
  sourceName: string
  sourceRef: string
  lastDownload: string | null
}

export function MethodologyDrawer({
  open,
  onClose,
  metricDefinition,
  sourceName,
  sourceRef,
  lastDownload,
}: MethodologyDrawerProps) {
  if (!open) return null

  return (
    <div className="drawer-overlay" role="presentation" onClick={onClose}>
      <aside
        className="drawer"
        role="dialog"
        aria-labelledby="methodology-title"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="drawer__header">
          <h2 id="methodology-title">Data methodology</h2>
          <button type="button" className="btn btn--ghost" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </header>
        <div className="drawer__body">
          <section>
            <h3>Metric</h3>
            <p>{metricDefinition}</p>
            <p>
              This is <strong>not</strong> actual flight, hotel, airport, or transport routing. It
              is the minimum great-circle distance between consecutive match venues.
            </p>
          </section>
          <section>
            <h3>Source</h3>
            <p>
              {sourceName} (ref: {sourceRef})
            </p>
            <p>Last download: {lastDownload ?? 'Unknown'}</p>
          </section>
          <section>
            <h3>Coordinate precision</h3>
            <p>
              Stadium coordinates are used when identifiable; city coordinates when only a host city
              is known. Unresolved venues are excluded from distance totals.
            </p>
          </section>
          <section>
            <h3>2026 fixtures</h3>
            <p>
              Scheduled matches contribute projected itinerary distance, distinct from completed
              travel.
            </p>
          </section>
        </div>
      </aside>
    </div>
  )
}
