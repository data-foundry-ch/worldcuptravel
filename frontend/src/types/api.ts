export interface TournamentSummary {
  year: number
  name: string | null
  match_count: number
  played_match_count: number
  team_count: number
  coordinate_coverage_pct: number
  unresolved_venue_count: number
}

export interface TeamSummary {
  team_id: string
  team_name: string
  match_count: number
  played_match_count: number
}

export interface MatchLocation {
  match_id: string
  sequence_number: number
  match_date: string | null
  kickoff_time_raw: string | null
  round_name: string | null
  opponent_name: string | null
  result: string | null
  raw_ground: string | null
  venue_id: string | null
  canonical_venue_name: string | null
  city: string | null
  country: string | null
  latitude: number | null
  longitude: number | null
  coordinate_precision: string | null
  leg_distance_km: number | null
  cumulative_distance_km: number
  is_played: boolean
  is_projected: boolean
  excluded_from_total: boolean
  exclusion_reason: string | null
}

export interface RouteLeg {
  leg_number: number
  from_match_id: string
  to_match_id: string
  from_latitude: number | null
  from_longitude: number | null
  to_latitude: number | null
  to_longitude: number | null
  from_date: string | null
  to_date: string | null
  distance_km: number | null
  cumulative_distance_km: number
  is_projected: boolean
  is_coordinate_complete: boolean
  excluded_from_total: boolean
  exclusion_reason: string | null
}

export interface RouteResponse {
  tournament_year: number
  team_id: string
  team_name: string
  scope: 'played' | 'all'
  metric_definition: string
  total_distance_km: number
  completed_distance_km: number
  projected_additional_distance_km: number
  match_count: number
  route_leg_count: number
  bounds: {
    min_lat: number | null
    max_lat: number | null
    min_lng: number | null
    max_lng: number | null
  }
  matches: MatchLocation[]
  legs: RouteLeg[]
  source_freshness: {
    last_download_timestamp: string | null
    last_dbt_build_timestamp: string | null
    is_stale: boolean
  }
  data_quality: {
    unresolved_match_count: number
    excluded_leg_count: number
    warnings: string[]
  }
}

export interface TournamentMovementPoint {
  venue_id: string
  label: string
  latitude: number
  longitude: number
  coordinate_precision: string | null
}

export interface TournamentMovementLeg {
  team_id: string
  team_name: string
  leg_number: number
  from_match_id: string
  to_match_id: string
  from_latitude: number
  from_longitude: number
  to_latitude: number
  to_longitude: number
  distance_km: number | null
  is_projected: boolean
}

export interface AllTournamentMovementPoint extends TournamentMovementPoint {
  tournament_year: number
}

export interface AllTournamentMovementLeg extends TournamentMovementLeg {
  tournament_year: number
}

export interface TournamentMovementsResponse {
  tournament_year: number
  scope: 'played' | 'all'
  total_distance_km: number
  point_count: number
  leg_count: number
  points: TournamentMovementPoint[]
  legs: TournamentMovementLeg[]
}

export interface AllTournamentMovementsResponse {
  scope: 'played' | 'all'
  total_distance_km: number
  tournament_count: number
  point_count: number
  leg_count: number
  team_count: number
  points: AllTournamentMovementPoint[]
  legs: AllTournamentMovementLeg[]
}

export interface TournamentTravelTotal {
  tournament_year: number
  total_distance_km: number
  completed_distance_km: number
  projected_additional_distance_km: number
  team_count: number
  leg_count: number
}

export interface LeaderboardEntry {
  rank: number
  team_id: string
  team_name: string
  total_distance_km: number
  completed_distance_km: number
  projected_additional_distance_km: number
  match_count: number
}

export interface LeaderboardResponse {
  tournament_year: number
  entries: LeaderboardEntry[]
}

export interface MetaResponse {
  application_version: string
  source_name: string
  source_ref: string
  last_successful_download_timestamp: string | null
  last_successful_dbt_build_timestamp: string | null
  available_tournament_range: number[]
  coordinate_coverage: {
    total_venues: number
    resolved_venues: number
    unresolved_venues: number
    coverage_pct: number
  }
  metric_definition: string
  data_freshness_warning_hours: number
  is_data_stale: boolean
}
