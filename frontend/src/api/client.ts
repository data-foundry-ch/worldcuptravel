const API_BASE = ''
const TIMEOUT_MS = 60000

async function fetchJson<T>(path: string): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)
  try {
    const res = await fetch(`${API_BASE}${path}`, { signal: controller.signal })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error((body as { detail?: string }).detail || `Request failed: ${res.status}`)
    }
    return (await res.json()) as T
  } finally {
    clearTimeout(timer)
  }
}

export const api = {
  meta: () => fetchJson<import('../types/api').MetaResponse>('/api/v1/meta'),
  tournaments: () => fetchJson<import('../types/api').TournamentSummary[]>('/api/v1/tournaments'),
  teams: (year: number) =>
    fetchJson<import('../types/api').TeamSummary[]>(`/api/v1/tournaments/${year}/teams`),
  route: (year: number, team: string, scope: 'played' | 'all') =>
    fetchJson<import('../types/api').RouteResponse>(
      `/api/v1/routes?year=${year}&team=${encodeURIComponent(team)}&scope=${scope}`,
    ),
  tournamentMovements: (year: number, scope: 'played' | 'all') =>
    fetchJson<import('../types/api').TournamentMovementsResponse>(
      `/api/v1/tournaments/${year}/movements?scope=${scope}`,
    ),
  allTournamentMovements: (scope: 'played' | 'all') =>
    fetchJson<import('../types/api').AllTournamentMovementsResponse>(
      `/api/v1/tournaments/movements?scope=${scope}`,
    ),
  tournamentTravelTotals: (scope: 'played' | 'all') =>
    fetchJson<import('../types/api').TournamentTravelTotal[]>(
      `/api/v1/tournaments/travel-totals?scope=${scope}`,
    ),
  leaderboard: (year: number, scope: 'played' | 'all') =>
    fetchJson<import('../types/api').LeaderboardResponse>(
      `/api/v1/tournaments/${year}/leaderboard?scope=${scope}`,
    ),
}
