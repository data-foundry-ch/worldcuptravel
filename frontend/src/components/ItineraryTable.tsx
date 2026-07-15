import type { MatchLocation } from '../types/api'
import { formatKm } from '../utils/haversine'

interface ItineraryTableProps {
  matches: MatchLocation[]
  onDownloadCsv: () => void
}

export function ItineraryTable({ matches, onDownloadCsv }: ItineraryTableProps) {
  if (!matches.length) {
    return <p className="empty-state">No matches to display for this selection.</p>
  }

  return (
    <div className="itinerary">
      <div className="itinerary__header">
        <h2>Chronological itinerary</h2>
        <button type="button" className="btn btn--ghost" onClick={onDownloadCsv}>
          Download CSV
        </button>
      </div>
      <div className="itinerary__scroll">
        <table>
          <thead>
            <tr>
              <th scope="col">#</th>
              <th scope="col">Date</th>
              <th scope="col">Round</th>
              <th scope="col">Opponent</th>
              <th scope="col">Result</th>
              <th scope="col">Location</th>
              <th scope="col">Leg km</th>
              <th scope="col">Cumulative km</th>
              <th scope="col">Precision</th>
            </tr>
          </thead>
          <tbody>
            {matches.map((m) => (
              <tr key={m.match_id} className={m.excluded_from_total ? 'row--warning' : ''}>
                <td>{m.sequence_number}</td>
                <td>{m.match_date ?? '—'}</td>
                <td>{m.round_name ?? '—'}</td>
                <td>{m.opponent_name ?? '—'}</td>
                <td>{m.result ?? '—'}</td>
                <td>{m.canonical_venue_name ?? m.raw_ground ?? '—'}</td>
                <td>{m.leg_distance_km != null ? formatKm(m.leg_distance_km) : '—'}</td>
                <td>{formatKm(m.cumulative_distance_km)}</td>
                <td>{m.coordinate_precision ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
