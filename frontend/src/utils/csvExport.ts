import type { MatchLocation } from '../types/api'

export function routeToCsv(matches: MatchLocation[], teamName: string, year: number): string {
  const headers = [
    'sequence',
    'date',
    'round',
    'opponent',
    'result',
    'location',
    'leg_distance_km',
    'cumulative_distance_km',
    'coordinate_precision',
  ]
  const rows = matches.map((m) => [
    m.sequence_number,
    m.match_date ?? '',
    m.round_name ?? '',
    m.opponent_name ?? '',
    m.result ?? '',
    m.canonical_venue_name ?? m.raw_ground ?? '',
    m.leg_distance_km ?? '',
    m.cumulative_distance_km,
    m.coordinate_precision ?? '',
  ])
  const escape = (v: string | number) => `"${String(v).replace(/"/g, '""')}"`
  const lines = [
    `# ${teamName} - World Cup ${year}`,
    headers.join(','),
    ...rows.map((r) => r.map(escape).join(',')),
  ]
  return lines.join('\n')
}

export function downloadCsv(content: string, filename: string) {
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
