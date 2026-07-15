import type { GlobeArc, GlobePoint } from './routeTransform'

export interface RouteKpi {
  label: string
  distanceKm?: number
  movementCount?: number
}

export type TravelKpiMetric =
  | 'totalTravel'
  | 'averageTravel'
  | 'averageLeg'
  | 'longestLeg'
  | 'locationCount'
  | 'mostRepeatedRoute'

export interface TravelKpiMetricConfig {
  id: TravelKpiMetric
  label: string
  unit: 'km' | 'locations' | 'movements'
}

export const TRAVEL_KPI_METRICS: TravelKpiMetricConfig[] = [
  { id: 'totalTravel', label: 'Total Travel Distance', unit: 'km' },
  { id: 'averageTravel', label: 'Average Travel Distance', unit: 'km' },
  { id: 'averageLeg', label: 'Average Travel Distance Per Leg', unit: 'km' },
  { id: 'longestLeg', label: 'Longest Single Leg', unit: 'km' },
  { id: 'locationCount', label: 'Number of Playing Locations', unit: 'locations' },
  { id: 'mostRepeatedRoute', label: 'Most Repeated Route', unit: 'movements' },
]

export interface TravelKpis {
  totalKm: number
  averageKm: number | null
  averageBasis: string
  averageLegKm: number | null
  longestSingleLeg: RouteKpi | null
  locationCount: number
  mostRepeatedRoute: RouteKpi | null
}

interface TravelKpiInput {
  totalKm: number
  averageDivisor: number
  averageBasis: string
  points: GlobePoint[]
  arcs: GlobeArc[]
}

function coordinateKey(lat: number, lng: number): string {
  return `${lat.toFixed(4)},${lng.toFixed(4)}`
}

function routeKey(arc: GlobeArc): string {
  const from = coordinateKey(arc.startLat, arc.startLng)
  const to = coordinateKey(arc.endLat, arc.endLng)
  return [from, to].sort().join('|')
}

function routeLabel(arc: GlobeArc, separator: string): string {
  return `${arc.startLabel} ${separator} ${arc.endLabel}`
}

function distinctLocationCount(points: GlobePoint[], arcs: GlobeArc[]): number {
  const locations = new Set<string>()

  arcs.forEach((arc) => {
    locations.add(coordinateKey(arc.startLat, arc.startLng))
    locations.add(coordinateKey(arc.endLat, arc.endLng))
  })

  if (locations.size > 0) return locations.size

  points.forEach((point) => locations.add(coordinateKey(point.lat, point.lng)))
  return locations.size
}

export function buildTravelKpis({
  totalKm,
  averageDivisor,
  averageBasis,
  points,
  arcs,
}: TravelKpiInput): TravelKpis {
  const arcsWithDistance = arcs.filter(
    (arc): arc is GlobeArc & { distanceKm: number } => arc.distanceKm != null,
  )
  const totalLegKm = arcsWithDistance.reduce((sum, arc) => sum + arc.distanceKm, 0)
  const longestSingleLeg = arcsWithDistance.reduce<RouteKpi | null>((longest, arc) => {
    if (longest && longest.distanceKm != null && longest.distanceKm >= arc.distanceKm) {
      return longest
    }
    return {
      label: `${arc.teamName}: ${routeLabel(arc, '→')}`,
      distanceKm: arc.distanceKm,
    }
  }, null)
  const repeatedRoutes = new Map<string, RouteKpi>()

  arcs.forEach((arc) => {
    const key = routeKey(arc)
    const existing = repeatedRoutes.get(key)

    if (existing) {
      repeatedRoutes.set(key, {
        ...existing,
        movementCount: (existing.movementCount ?? 0) + 1,
      })
      return
    }

    repeatedRoutes.set(key, {
      label: routeLabel(arc, '↔'),
      movementCount: 1,
    })
  })

  const mostRepeatedRoute = [...repeatedRoutes.values()].reduce<RouteKpi | null>((most, route) => {
    if (most && (most.movementCount ?? 0) >= (route.movementCount ?? 0)) return most
    return route
  }, null)

  return {
    totalKm,
    averageKm: averageDivisor > 0 ? totalKm / averageDivisor : null,
    averageBasis,
    averageLegKm: arcsWithDistance.length > 0 ? totalLegKm / arcsWithDistance.length : null,
    longestSingleLeg,
    locationCount: distinctLocationCount(points, arcs),
    mostRepeatedRoute,
  }
}

export function getTravelKpiMetricConfig(metric: TravelKpiMetric): TravelKpiMetricConfig {
  return TRAVEL_KPI_METRICS.find((config) => config.id === metric) ?? TRAVEL_KPI_METRICS[0]
}

export function getTravelKpiMetricValue(kpis: TravelKpis, metric: TravelKpiMetric): number | null {
  switch (metric) {
    case 'totalTravel':
      return kpis.totalKm
    case 'averageTravel':
      return kpis.averageKm
    case 'averageLeg':
      return kpis.averageLegKm
    case 'longestLeg':
      return kpis.longestSingleLeg?.distanceKm ?? null
    case 'locationCount':
      return kpis.locationCount
    case 'mostRepeatedRoute':
      return kpis.mostRepeatedRoute?.movementCount ?? null
  }
}
