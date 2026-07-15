import type {
  AllTournamentMovementsResponse,
  RouteLeg,
  RouteResponse,
  TournamentMovementsResponse,
} from '../types/api'

export interface GlobePoint {
  id: string
  lat: number
  lng: number
  label: string
  sequence: number
  isProjected: boolean
  tournamentYear?: number
}

export interface GlobeArc {
  id: string
  teamName: string
  startLabel: string
  endLabel: string
  startLat: number
  startLng: number
  endLat: number
  endLng: number
  legNumber: number
  distanceKm: number | null
  cumulativeKm: number
  isProjected: boolean
  isComplete: boolean
  duplicateIndex: number
  duplicateCount: number
  arcAltitude: number
  tournamentYear?: number
}

const MIN_ARC_ALTITUDE = 0.025
const MAX_DISTANCE_ARC_ALTITUDE = 0.26
const DEFAULT_ARC_ALTITUDE = 0.08
const ARC_ALTITUDE_DISTANCE_CAP_KM = 12000
const ARC_FAN_STEP = 0.006
const MAX_ARC_FAN_OFFSET = 0.045

function coordinateKey(lat: number, lng: number): string {
  return `${lat.toFixed(4)},${lng.toFixed(4)}`
}

function fallbackVenueLabel(matchId: string): string {
  return `Match ${matchId}`
}

function routePairKey(arc: Pick<GlobeArc, 'startLat' | 'startLng' | 'endLat' | 'endLng'>): string {
  const from = coordinateKey(arc.startLat, arc.startLng)
  const to = coordinateKey(arc.endLat, arc.endLng)
  return [from, to].sort().join('|')
}

function yearCoordinateKey(year: number, lat: number, lng: number): string {
  return `${year}:${coordinateKey(lat, lng)}`
}

function distanceArcAltitude(distanceKm: number | null): number {
  if (distanceKm == null) return DEFAULT_ARC_ALTITUDE

  const normalizedDistance = Math.min(Math.max(distanceKm, 0), ARC_ALTITUDE_DISTANCE_CAP_KM)
  const distanceCurve = Math.sqrt(normalizedDistance / ARC_ALTITUDE_DISTANCE_CAP_KM)
  return MIN_ARC_ALTITUDE + distanceCurve * (MAX_DISTANCE_ARC_ALTITUDE - MIN_ARC_ALTITUDE)
}

function withDuplicateArcFan(arcs: Omit<GlobeArc, 'duplicateIndex' | 'duplicateCount' | 'arcAltitude'>[]): GlobeArc[] {
  const groups = new Map<string, number[]>()

  arcs.forEach((arc, index) => {
    const key = routePairKey(arc)
    groups.set(key, [...(groups.get(key) ?? []), index])
  })

  return arcs.map((arc, index) => {
    const group = groups.get(routePairKey(arc)) ?? [index]
    const duplicateIndex = group.indexOf(index)
    const duplicateCount = group.length
    const fanOffset = Math.min(MAX_ARC_FAN_OFFSET, duplicateIndex * ARC_FAN_STEP)

    return {
      ...arc,
      duplicateIndex,
      duplicateCount,
      arcAltitude: distanceArcAltitude(arc.distanceKm) + fanOffset,
    }
  })
}

export function buildGlobeData(route: RouteResponse | undefined): {
  points: GlobePoint[]
  arcs: GlobeArc[]
} {
  if (!route) return { points: [], arcs: [] }

  const points: GlobePoint[] = route.matches
    .filter((m) => m.latitude != null && m.longitude != null)
    .map((m) => ({
      id: m.match_id,
      lat: m.latitude as number,
      lng: m.longitude as number,
      label: m.canonical_venue_name ?? m.raw_ground ?? `Match ${m.sequence_number}`,
      sequence: m.sequence_number,
      isProjected: m.is_projected,
    }))
  const matchLabels = new Map(
    route.matches.map((m) => [
      m.match_id,
      m.canonical_venue_name ?? m.raw_ground ?? fallbackVenueLabel(m.match_id),
    ]),
  )

  const arcs = route.legs
    .filter(
      (l: RouteLeg) =>
        l.from_latitude != null &&
        l.from_longitude != null &&
        l.to_latitude != null &&
        l.to_longitude != null,
    )
    .map((l) => ({
      id: `${l.from_match_id}-${l.to_match_id}`,
      teamName: route.team_name,
      startLabel: matchLabels.get(l.from_match_id) ?? fallbackVenueLabel(l.from_match_id),
      endLabel: matchLabels.get(l.to_match_id) ?? fallbackVenueLabel(l.to_match_id),
      startLat: l.from_latitude as number,
      startLng: l.from_longitude as number,
      endLat: l.to_latitude as number,
      endLng: l.to_longitude as number,
      legNumber: l.leg_number,
      distanceKm: l.distance_km,
      cumulativeKm: l.cumulative_distance_km,
      isProjected: l.is_projected,
      isComplete: l.is_coordinate_complete,
    }))

  return { points, arcs: withDuplicateArcFan(arcs) }
}

export function buildTournamentMovementsGlobeData(
  movements: TournamentMovementsResponse | undefined,
): {
  points: GlobePoint[]
  arcs: GlobeArc[]
} {
  if (!movements) return { points: [], arcs: [] }

  const points: GlobePoint[] = movements.points.map((p, index) => ({
    id: p.venue_id,
    lat: p.latitude,
    lng: p.longitude,
    label: p.label,
    sequence: index + 1,
    isProjected: false,
  }))
  const pointLabels = new Map(points.map((p) => [coordinateKey(p.lat, p.lng), p.label]))

  const arcs = movements.legs.map((l, index) => ({
    id: `${l.team_id}-${l.from_match_id}-${l.to_match_id}`,
    teamName: l.team_name,
    startLabel: pointLabels.get(coordinateKey(l.from_latitude, l.from_longitude)) ?? fallbackVenueLabel(l.from_match_id),
    endLabel: pointLabels.get(coordinateKey(l.to_latitude, l.to_longitude)) ?? fallbackVenueLabel(l.to_match_id),
    startLat: l.from_latitude,
    startLng: l.from_longitude,
    endLat: l.to_latitude,
    endLng: l.to_longitude,
    legNumber: index + 1,
    distanceKm: l.distance_km,
    cumulativeKm: 0,
    isProjected: l.is_projected,
    isComplete: true,
  }))

  return { points, arcs: withDuplicateArcFan(arcs) }
}

export function buildAllTournamentMovementsGlobeData(
  movements: AllTournamentMovementsResponse | undefined,
): {
  points: GlobePoint[]
  arcs: GlobeArc[]
} {
  if (!movements) return { points: [], arcs: [] }

  const points: GlobePoint[] = movements.points.map((p, index) => ({
    id: `${p.tournament_year}-${p.venue_id}`,
    lat: p.latitude,
    lng: p.longitude,
    label: `${p.label} (${p.tournament_year})`,
    sequence: index + 1,
    isProjected: false,
    tournamentYear: p.tournament_year,
  }))
  const pointLabels = new Map(
    movements.points.map((p) => [
      yearCoordinateKey(p.tournament_year, p.latitude, p.longitude),
      p.label,
    ]),
  )

  const arcs = movements.legs.map((l, index) => ({
    id: `${l.tournament_year}-${l.team_id}-${l.from_match_id}-${l.to_match_id}`,
    teamName: l.team_name,
    startLabel:
      pointLabels.get(yearCoordinateKey(l.tournament_year, l.from_latitude, l.from_longitude)) ??
      fallbackVenueLabel(l.from_match_id),
    endLabel:
      pointLabels.get(yearCoordinateKey(l.tournament_year, l.to_latitude, l.to_longitude)) ??
      fallbackVenueLabel(l.to_match_id),
    startLat: l.from_latitude,
    startLng: l.from_longitude,
    endLat: l.to_latitude,
    endLng: l.to_longitude,
    legNumber: index + 1,
    distanceKm: l.distance_km,
    cumulativeKm: 0,
    isProjected: l.is_projected,
    isComplete: true,
    tournamentYear: l.tournament_year,
  }))

  return { points, arcs: withDuplicateArcFan(arcs) }
}
