import { QueryClient, QueryClientProvider, useQueries, useQuery } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'
import { api } from './api/client'
import { ControlsPanel } from './components/ControlsPanel'
import { DataQualityBanner } from './components/DataQualityBanner'
import { GlobeView } from './components/GlobeView'
import { ItineraryTable } from './components/ItineraryTable'
import { MethodologyDrawer } from './components/MethodologyDrawer'
import type { TeamChartEntry } from './components/TeamTravelChart'
import { TeamTravelChart } from './components/TeamTravelChart'
import { TravelKpiPanel } from './components/TravelKpiPanel'
import type { YearChartEntry } from './components/YearTravelChart'
import { YearTravelChart } from './components/YearTravelChart'
import type { AllTournamentMovementsResponse, RouteResponse, TournamentMovementsResponse } from './types/api'
import { useUrlState } from './hooks/useUrlState'
import { downloadCsv, routeToCsv } from './utils/csvExport'
import { formatKm } from './utils/haversine'
import {
  buildAllTournamentMovementsGlobeData,
  buildGlobeData,
  buildTournamentMovementsGlobeData,
} from './utils/routeTransform'
import {
  buildTravelKpis,
  getTravelKpiMetricConfig,
  getTravelKpiMetricValue,
  type TravelKpiMetric,
} from './utils/travelKpis'
import './App.css'

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 60_000, retry: 1 } },
})
const DEFAULT_SCOPE = 'all' as const
const DEFAULT_YEAR = 2026
const MOVEMENT_DETAIL_METRICS: TravelKpiMetric[] = ['longestLeg', 'locationCount', 'mostRepeatedRoute']

function formatCount(value: number): string {
  return value.toLocaleString('en-US')
}

function formatMetricValue(value: number, metric: TravelKpiMetric): string {
  const unit = getTravelKpiMetricConfig(metric).unit
  return unit === 'km' ? formatKm(value) : formatCount(value)
}

function routeKpis(route: RouteResponse) {
  const { points, arcs } = buildGlobeData(route)
  return buildTravelKpis({
    totalKm: route.total_distance_km,
    averageDivisor: route.match_count,
    averageBasis: 'Per match',
    points,
    arcs,
  })
}

function tournamentMovementKpis(movements: TournamentMovementsResponse, averageDivisor: number) {
  const { points, arcs } = buildTournamentMovementsGlobeData(movements)
  return buildTravelKpis({
    totalKm: movements.total_distance_km,
    averageDivisor,
    averageBasis: 'Per team',
    points,
    arcs,
  })
}

interface AllYearsTeamAggregate {
  teamId: string
  teamName: string
  totalKm: number
  legCount: number
  tournamentYears: Set<number>
  locations: Set<string>
  routes: Map<string, { label: string; count: number }>
  longestLeg: { label: string; distanceKm: number } | null
}

function coordinateKey(lat: number, lng: number): string {
  return `${lat.toFixed(4)},${lng.toFixed(4)}`
}

function routeKey(fromLat: number, fromLng: number, toLat: number, toLng: number): string {
  const from = coordinateKey(fromLat, fromLng)
  const to = coordinateKey(toLat, toLng)
  return [from, to].sort().join('|')
}

function buildAllYearsTeamEntries(
  movements: AllTournamentMovementsResponse,
  selectedMetric: TravelKpiMetric,
): TeamChartEntry[] {
  const aggregates = new Map<string, AllYearsTeamAggregate>()
  const pointLabels = new Map(
    movements.points.map((point) => [
      `${point.tournament_year}:${coordinateKey(point.latitude, point.longitude)}`,
      point.label,
    ]),
  )

  movements.legs.forEach((leg) => {
    const distanceKm = leg.distance_km ?? 0
    const aggregate =
      aggregates.get(leg.team_id) ??
      {
        teamId: leg.team_id,
        teamName: leg.team_name,
        totalKm: 0,
        legCount: 0,
        tournamentYears: new Set<number>(),
        locations: new Set<string>(),
        routes: new Map<string, { label: string; count: number }>(),
        longestLeg: null,
      }
    const startLabel =
      pointLabels.get(`${leg.tournament_year}:${coordinateKey(leg.from_latitude, leg.from_longitude)}`) ??
      `Match ${leg.from_match_id}`
    const endLabel =
      pointLabels.get(`${leg.tournament_year}:${coordinateKey(leg.to_latitude, leg.to_longitude)}`) ??
      `Match ${leg.to_match_id}`
    const route = routeKey(leg.from_latitude, leg.from_longitude, leg.to_latitude, leg.to_longitude)
    const existingRoute = aggregate.routes.get(route)

    aggregate.totalKm += distanceKm
    aggregate.legCount += 1
    aggregate.tournamentYears.add(leg.tournament_year)
    aggregate.locations.add(coordinateKey(leg.from_latitude, leg.from_longitude))
    aggregate.locations.add(coordinateKey(leg.to_latitude, leg.to_longitude))
    aggregate.routes.set(route, {
      label: existingRoute?.label ?? `${startLabel} ↔ ${endLabel}`,
      count: (existingRoute?.count ?? 0) + 1,
    })

    if (!aggregate.longestLeg || aggregate.longestLeg.distanceKm < distanceKm) {
      aggregate.longestLeg = {
        label: `${leg.tournament_year} · ${leg.team_name}: ${startLabel} → ${endLabel}`,
        distanceKm,
      }
    }

    aggregates.set(leg.team_id, aggregate)
  })

  return [...aggregates.values()]
    .map((aggregate) => {
      const mostRepeatedRoute = [...aggregate.routes.values()].reduce<{ label: string; count: number } | null>(
        (most, route) => (!most || route.count > most.count ? route : most),
        null,
      )
      const value =
        selectedMetric === 'totalTravel' || selectedMetric === 'averageTravel'
          ? aggregate.totalKm
          : selectedMetric === 'averageLeg'
            ? aggregate.legCount > 0
              ? aggregate.totalKm / aggregate.legCount
              : 0
            : selectedMetric === 'longestLeg'
              ? (aggregate.longestLeg?.distanceKm ?? 0)
              : selectedMetric === 'locationCount'
                ? aggregate.locations.size
                : (mostRepeatedRoute?.count ?? 0)

      return {
        teamId: aggregate.teamId,
        teamName: aggregate.teamName,
        value,
        valueLabel: formatMetricValue(value, selectedMetric),
        detail:
          selectedMetric === 'longestLeg'
            ? aggregate.longestLeg?.label
            : selectedMetric === 'mostRepeatedRoute'
              ? mostRepeatedRoute?.label
              : undefined,
      }
    })
    .sort((a, b) => b.value - a.value || a.teamName.localeCompare(b.teamName))
}

function sortTeamChartEntries(entries: TeamChartEntry[]): TeamChartEntry[] {
  return [...entries].sort((a, b) => b.value - a.value || a.teamName.localeCompare(b.teamName))
}

function Dashboard() {
  const [urlState, setUrlState] = useUrlState()
  const [itineraryOpen, setItineraryOpen] = useState(false)
  const [methodologyOpen, setMethodologyOpen] = useState(false)
  const [logoAvailable, setLogoAvailable] = useState(true)
  const [selectedMetric, setSelectedMetric] = useState<TravelKpiMetric>('totalTravel')
  const isAllYears = urlState.year === 'all'
  const selectedYear = typeof urlState.year === 'number' ? urlState.year : null

  const reducedMotion = useMemo(
    () => window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    [],
  )

  const metaQuery = useQuery({ queryKey: ['meta'], queryFn: api.meta })
  const teamsQuery = useQuery({
    queryKey: ['teams', urlState.year],
    queryFn: () => api.teams(selectedYear as number),
    enabled: selectedYear != null,
  })

  const routeQuery = useQuery({
    queryKey: ['route', urlState.year, urlState.team, DEFAULT_SCOPE],
    queryFn: () => api.route(selectedYear as number, urlState.team as string, DEFAULT_SCOPE),
    enabled: selectedYear != null && !!urlState.team,
  })

  const movementsQuery = useQuery({
    queryKey: ['tournament-movements', urlState.year, DEFAULT_SCOPE],
    queryFn: () => api.tournamentMovements(selectedYear as number, DEFAULT_SCOPE),
    enabled: selectedYear != null && !urlState.team,
  })

  const allMovementsQuery = useQuery({
    queryKey: ['all-tournament-movements', DEFAULT_SCOPE],
    queryFn: () => api.allTournamentMovements(DEFAULT_SCOPE),
    enabled: isAllYears || selectedMetric === 'averageTravel' || MOVEMENT_DETAIL_METRICS.includes(selectedMetric),
  })

  const travelTotalsQuery = useQuery({
    queryKey: ['tournament-travel-totals', DEFAULT_SCOPE],
    queryFn: () => api.tournamentTravelTotals(DEFAULT_SCOPE),
  })

  const leaderboardQuery = useQuery({
    queryKey: ['leaderboard', urlState.year, DEFAULT_SCOPE],
    queryFn: () => api.leaderboard(selectedYear as number, DEFAULT_SCOPE),
    enabled: selectedYear != null,
  })
  const needsTeamRoutes =
    selectedMetric !== 'totalTravel' && selectedMetric !== 'averageTravel'
  const needsYearMovements = MOVEMENT_DETAIL_METRICS.includes(selectedMetric)
  const teamRouteQueries = useQueries({
    queries: (teamsQuery.data ?? []).map((team) => ({
      queryKey: ['route', urlState.year, team.team_id, DEFAULT_SCOPE, 'metric-chart'],
      queryFn: () => api.route(selectedYear as number, team.team_id, DEFAULT_SCOPE),
      enabled: selectedYear != null && needsTeamRoutes,
    })),
  })
  const yearMovementQueries = useQueries({
    queries: (travelTotalsQuery.data ?? []).map((total) => ({
      queryKey: ['tournament-movements', total.tournament_year, DEFAULT_SCOPE, 'metric-chart'],
      queryFn: () => api.tournamentMovements(total.tournament_year, DEFAULT_SCOPE),
      enabled: needsYearMovements,
    })),
  })

  const { points, arcs } = useMemo(() => {
    if (isAllYears) return buildAllTournamentMovementsGlobeData(allMovementsQuery.data)
    if (urlState.team) return buildGlobeData(routeQuery.data)
    return buildTournamentMovementsGlobeData(movementsQuery.data)
  }, [allMovementsQuery.data, isAllYears, movementsQuery.data, routeQuery.data, urlState.team])
  const totalTravelKm = isAllYears
    ? (allMovementsQuery.data?.total_distance_km ?? 0)
    : urlState.team
    ? (routeQuery.data?.total_distance_km ?? 0)
    : (movementsQuery.data?.total_distance_km ?? 0)
  const averageDivisor = isAllYears
    ? (allMovementsQuery.data?.team_count ?? 0)
    : urlState.team
    ? (routeQuery.data?.match_count ?? 0)
    : (leaderboardQuery.data?.entries.length ?? new Set(arcs.map((arc) => arc.teamName)).size)
  const travelKpis = useMemo(
    () =>
      buildTravelKpis({
        totalKm: totalTravelKm,
        averageDivisor,
        averageBasis: urlState.team && !isAllYears ? 'Per match' : 'Per team',
        points,
        arcs,
      }),
    [arcs, averageDivisor, isAllYears, points, totalTravelKm, urlState.team],
  )
  const selectedMetricConfig = getTravelKpiMetricConfig(selectedMetric)
  const teamChartMetricLabel =
    selectedMetric === 'averageTravel' ? 'Distance per team' : selectedMetricConfig.label
  const yearChartMetricLabel =
    selectedMetric === 'averageTravel' ? 'Average per team' : selectedMetricConfig.label
  const teamChartEntries = useMemo<TeamChartEntry[] | undefined>(() => {
    if (isAllYears) {
      const movements = allMovementsQuery.data
      if (!movements) return undefined

      return buildAllYearsTeamEntries(movements, selectedMetric)
    }

    if (selectedMetric === 'totalTravel' || selectedMetric === 'averageTravel') {
      const entries = leaderboardQuery.data?.entries.map((entry) => ({
        teamId: entry.team_id,
        teamName: entry.team_name,
        value: entry.total_distance_km,
        valueLabel: formatMetricValue(entry.total_distance_km, 'totalTravel'),
      }))
      return entries ? sortTeamChartEntries(entries) : undefined
    }

    const entries: TeamChartEntry[] = []

    teamRouteQueries.forEach((query, index) => {
      const route = query.data
      const team = teamsQuery.data?.[index]
      if (!route || !team) return

      const kpis = routeKpis(route)
      const value = getTravelKpiMetricValue(kpis, selectedMetric)
      if (value == null) return

      entries.push({
        teamId: team.team_id,
        teamName: team.team_name,
        value,
        valueLabel: formatMetricValue(value, selectedMetric),
        detail:
          selectedMetric === 'longestLeg'
            ? kpis.longestSingleLeg?.label
            : selectedMetric === 'mostRepeatedRoute'
              ? kpis.mostRepeatedRoute?.label
              : undefined,
      })
    })

    return sortTeamChartEntries(entries)
  }, [
    allMovementsQuery.data,
    isAllYears,
    leaderboardQuery.data?.entries,
    selectedMetric,
    teamRouteQueries,
    teamsQuery.data,
  ])
  const yearChartEntries = useMemo<YearChartEntry[] | undefined>(() => {
    const totals = travelTotalsQuery.data
    if (!totals?.length) return undefined

    if (selectedMetric === 'totalTravel') {
      return totals.map((total) => ({
        year: total.tournament_year,
        value: total.total_distance_km,
        valueLabel: formatMetricValue(total.total_distance_km, selectedMetric),
      }))
    }

    if (selectedMetric === 'averageTravel') {
      return totals.map((total) => {
        const value = total.team_count > 0 ? total.total_distance_km / total.team_count : 0
        return {
          year: total.tournament_year,
          value,
          valueLabel: formatMetricValue(value, selectedMetric),
        }
      })
    }

    if (selectedMetric === 'averageLeg') {
      return totals.map((total) => {
        const value = total.leg_count > 0 ? total.total_distance_km / total.leg_count : 0
        return {
          year: total.tournament_year,
          value,
          valueLabel: formatMetricValue(value, selectedMetric),
        }
      })
    }

    const entries: YearChartEntry[] = []

    yearMovementQueries.forEach((query, index) => {
      const movements = query.data
      const total = totals[index]
      if (!movements || !total) return

      const kpis = tournamentMovementKpis(movements, total.team_count)
      const value = getTravelKpiMetricValue(kpis, selectedMetric)
      if (value == null) return

      entries.push({
        year: total.tournament_year,
        value,
        valueLabel: formatMetricValue(value, selectedMetric),
        detail:
          selectedMetric === 'longestLeg'
            ? kpis.longestSingleLeg?.label
            : selectedMetric === 'mostRepeatedRoute'
              ? kpis.mostRepeatedRoute?.label
              : undefined,
      })
    })

    return entries
  }, [selectedMetric, travelTotalsQuery.data, yearMovementQueries])

  // Default to the latest tournament with usable played-route data, but let users explicitly choose a year/team.
  useEffect(() => {
    if (!urlState.year) {
      setUrlState({ year: DEFAULT_YEAR })
    }
  }, [setUrlState, urlState.year])

  // Validate team/year combo
  useEffect(() => {
    if (urlState.team && teamsQuery.data && !teamsQuery.data.some((t) => t.team_id === urlState.team)) {
      setUrlState({ team: null })
    }
  }, [teamsQuery.data, urlState.team, setUrlState])

  const routeError =
    routeQuery.error instanceof Error
      ? routeQuery.error.message
      : allMovementsQuery.error instanceof Error
        ? allMovementsQuery.error.message
        : movementsQuery.error instanceof Error
          ? movementsQuery.error.message
          : leaderboardQuery.error instanceof Error
            ? leaderboardQuery.error.message
            : teamsQuery.error instanceof Error
              ? teamsQuery.error.message
              : null

  const handleCsvDownload = () => {
    if (!routeQuery.data) return
    const csv = routeToCsv(
      routeQuery.data.matches,
      routeQuery.data.team_name,
      routeQuery.data.tournament_year,
    )
    downloadCsv(csv, `worldcup-${routeQuery.data.tournament_year}-${routeQuery.data.team_id}.csv`)
  }

  const handleYearSelect = (year: number | 'all') => {
    setUrlState({ year, team: null })
  }

  const handleTeamSelect = (teamId: string | null) => {
    if (isAllYears) return
    setUrlState({ team: teamId })
  }

  return (
    <div className="app-shell">
      <div className="globe-layer">
        <GlobeView
          points={points}
          arcs={arcs}
          onPointClick={() => undefined}
          reducedMotion={reducedMotion}
        />
      </div>

      <aside className="overlay overlay--left">
        <ControlsPanel
          meta={metaQuery.data}
          year={urlState.year}
          team={urlState.team}
          error={routeError}
          itineraryOpen={itineraryOpen}
          onToggleItinerary={() => setItineraryOpen((o) => !o)}
          onOpenMethodology={() => setMethodologyOpen(true)}
        />
        <TeamTravelChart
          entries={teamChartEntries}
          selectedTeamId={isAllYears ? null : urlState.team}
          metricLabel={teamChartMetricLabel}
          onSelectTeam={handleTeamSelect}
        />
      </aside>

      <aside className="year-chart-panel">
        <YearTravelChart
          entries={yearChartEntries}
          selectedYear={urlState.year}
          metricLabel={yearChartMetricLabel}
          onSelectYear={handleYearSelect}
        />
      </aside>

      <aside className="overlay overlay--right">
        <a
          className="logo-slot"
          href="https://www.datafoundry.ch"
          target="_blank"
          rel="noreferrer"
          aria-label="Open Datafoundry website"
        >
          {logoAvailable ? (
            <img
              src="/logo.png"
              alt="World Cup Travel Atlas logo"
              onError={() => setLogoAvailable(false)}
              onLoad={() => setLogoAvailable(true)}
            />
          ) : (
            <span>Logo</span>
          )}
        </a>
        <TravelKpiPanel
          kpis={travelKpis}
          selectedMetric={selectedMetric}
          onSelectMetric={setSelectedMetric}
        />
        {urlState.team && routeQuery.data && (
          <DataQualityBanner
            warnings={routeQuery.data.data_quality.warnings}
            isStale={routeQuery.data.source_freshness.is_stale}
            unresolvedCount={routeQuery.data.data_quality.unresolved_match_count}
          />
        )}
      </aside>

      {itineraryOpen && (
        <section className={`itinerary-panel ${itineraryOpen ? 'open' : ''}`}>
          {routeQuery.isLoading ? (
            <p className="empty-state">Loading route…</p>
          ) : (
            <ItineraryTable
              matches={urlState.team ? (routeQuery.data?.matches ?? []) : []}
              onDownloadCsv={handleCsvDownload}
            />
          )}
        </section>
      )}

      <MethodologyDrawer
        open={methodologyOpen}
        onClose={() => setMethodologyOpen(false)}
        metricDefinition={metaQuery.data?.metric_definition ?? ''}
        sourceName={metaQuery.data?.source_name ?? 'OpenFootball'}
        sourceRef={metaQuery.data?.source_ref ?? 'master'}
        lastDownload={metaQuery.data?.last_successful_download_timestamp ?? null}
      />
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Dashboard />
    </QueryClientProvider>
  )
}
