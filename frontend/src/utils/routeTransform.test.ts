import { describe, expect, it } from 'vitest'
import {
  buildAllTournamentMovementsGlobeData,
  buildGlobeData,
  buildTournamentMovementsGlobeData,
} from '../utils/routeTransform'
import type { AllTournamentMovementsResponse, RouteResponse, TournamentMovementsResponse } from '../types/api'

const sampleRoute: RouteResponse = {
  tournament_year: 1930,
  team_id: 'uruguay',
  team_name: 'Uruguay',
  scope: 'played',
  metric_definition: 'test',
  total_distance_km: 5,
  completed_distance_km: 5,
  projected_additional_distance_km: 0,
  match_count: 2,
  route_leg_count: 1,
  bounds: { min_lat: -35, max_lat: -34, min_lng: -57, max_lng: -56 },
  matches: [
    {
      match_id: 'a',
      sequence_number: 1,
      match_date: '1930-07-13',
      kickoff_time_raw: null,
      round_name: 'Group',
      opponent_name: 'Peru',
      result: 'win',
      raw_ground: 'Centenario',
      venue_id: 'v1',
      canonical_venue_name: 'Centenario',
      city: 'Montevideo',
      country: 'Uruguay',
      latitude: -34.89,
      longitude: -56.15,
      coordinate_precision: 'stadium',
      leg_distance_km: 0,
      cumulative_distance_km: 0,
      is_played: true,
      is_projected: false,
      excluded_from_total: false,
      exclusion_reason: null,
    },
    {
      match_id: 'b',
      sequence_number: 2,
      match_date: '1930-07-19',
      kickoff_time_raw: null,
      round_name: 'Group',
      opponent_name: 'Peru',
      result: 'win',
      raw_ground: 'Pocitos',
      venue_id: 'v2',
      canonical_venue_name: 'Pocitos',
      city: 'Montevideo',
      country: 'Uruguay',
      latitude: -34.91,
      longitude: -56.15,
      coordinate_precision: 'stadium',
      leg_distance_km: 2.2,
      cumulative_distance_km: 2.2,
      is_played: true,
      is_projected: false,
      excluded_from_total: false,
      exclusion_reason: null,
    },
  ],
  legs: [
    {
      leg_number: 1,
      from_match_id: 'a',
      to_match_id: 'b',
      from_latitude: -34.89,
      from_longitude: -56.15,
      to_latitude: -34.91,
      to_longitude: -56.15,
      from_date: '1930-07-13',
      to_date: '1930-07-19',
      distance_km: 2.2,
      cumulative_distance_km: 2.2,
      is_projected: false,
      is_coordinate_complete: true,
      excluded_from_total: false,
      exclusion_reason: null,
    },
  ],
  source_freshness: {
    last_download_timestamp: null,
    last_dbt_build_timestamp: null,
    is_stale: false,
  },
  data_quality: { unresolved_match_count: 0, excluded_leg_count: 0, warnings: [] },
}

describe('buildGlobeData', () => {
  it('creates points and arcs from route', () => {
    const { points, arcs } = buildGlobeData(sampleRoute)
    expect(points).toHaveLength(2)
    expect(arcs).toHaveLength(1)
    expect(arcs[0].distanceKm).toBe(2.2)
    expect(arcs[0].teamName).toBe('Uruguay')
    expect(arcs[0].startLabel).toBe('Centenario')
    expect(arcs[0].endLabel).toBe('Pocitos')
  })

  it('handles undefined route', () => {
    const { points, arcs } = buildGlobeData(undefined)
    expect(points).toHaveLength(0)
    expect(arcs).toHaveLength(0)
  })

  it('fans duplicate tournament movement arcs by altitude', () => {
    const movements: TournamentMovementsResponse = {
      tournament_year: 1930,
      scope: 'played',
      total_distance_km: 6.6,
      point_count: 2,
      leg_count: 3,
      points: [
        {
          venue_id: 'v1',
          label: 'Centenario',
          latitude: -34.89,
          longitude: -56.15,
          coordinate_precision: 'stadium',
        },
        {
          venue_id: 'v2',
          label: 'Pocitos',
          latitude: -34.91,
          longitude: -56.15,
          coordinate_precision: 'stadium',
        },
      ],
      legs: [
        {
          team_id: 'a',
          team_name: 'Team A',
          leg_number: 1,
          from_match_id: 'a1',
          to_match_id: 'a2',
          from_latitude: -34.89,
          from_longitude: -56.15,
          to_latitude: -34.91,
          to_longitude: -56.15,
          distance_km: 2.2,
          is_projected: false,
        },
        {
          team_id: 'b',
          team_name: 'Team B',
          leg_number: 1,
          from_match_id: 'b1',
          to_match_id: 'b2',
          from_latitude: -34.89,
          from_longitude: -56.15,
          to_latitude: -34.91,
          to_longitude: -56.15,
          distance_km: 2.2,
          is_projected: false,
        },
        {
          team_id: 'c',
          team_name: 'Team C',
          leg_number: 1,
          from_match_id: 'c1',
          to_match_id: 'c2',
          from_latitude: -34.91,
          from_longitude: -56.15,
          to_latitude: -34.89,
          to_longitude: -56.15,
          distance_km: 2.2,
          is_projected: false,
        },
      ],
    }

    const { arcs } = buildTournamentMovementsGlobeData(movements)

    expect(arcs).toHaveLength(3)
    expect(arcs.map((arc) => arc.duplicateCount)).toEqual([3, 3, 3])
    expect(new Set(arcs.map((arc) => arc.arcAltitude)).size).toBe(3)
    expect(arcs[0].teamName).toBe('Team A')
    expect(arcs[0].startLabel).toBe('Centenario')
    expect(arcs[0].endLabel).toBe('Pocitos')
  })

  it('scales arc altitude with travel distance', () => {
    const movements: TournamentMovementsResponse = {
      tournament_year: 1930,
      scope: 'played',
      total_distance_km: 4002.2,
      point_count: 3,
      leg_count: 2,
      points: [
        {
          venue_id: 'v1',
          label: 'Venue A',
          latitude: -34.89,
          longitude: -56.15,
          coordinate_precision: 'stadium',
        },
        {
          venue_id: 'v2',
          label: 'Venue B',
          latitude: -34.91,
          longitude: -56.15,
          coordinate_precision: 'stadium',
        },
        {
          venue_id: 'v3',
          label: 'Venue C',
          latitude: 40.71,
          longitude: -74.01,
          coordinate_precision: 'stadium',
        },
      ],
      legs: [
        {
          team_id: 'a',
          team_name: 'Team A',
          leg_number: 1,
          from_match_id: 'a1',
          to_match_id: 'a2',
          from_latitude: -34.89,
          from_longitude: -56.15,
          to_latitude: -34.91,
          to_longitude: -56.15,
          distance_km: 2.2,
          is_projected: false,
        },
        {
          team_id: 'a',
          team_name: 'Team A',
          leg_number: 2,
          from_match_id: 'a2',
          to_match_id: 'a3',
          from_latitude: -34.91,
          from_longitude: -56.15,
          to_latitude: 40.71,
          to_longitude: -74.01,
          distance_km: 4000,
          is_projected: false,
        },
      ],
    }

    const { arcs } = buildTournamentMovementsGlobeData(movements)

    expect(arcs[0].arcAltitude).toBeLessThan(0.04)
    expect(arcs[1].arcAltitude).toBeGreaterThan(arcs[0].arcAltitude)
  })

  it('creates year-aware points and arcs for all tournament movements', () => {
    const movements: AllTournamentMovementsResponse = {
      scope: 'played',
      total_distance_km: 2.2,
      tournament_count: 2,
      point_count: 2,
      leg_count: 1,
      team_count: 1,
      points: [
        {
          tournament_year: 1930,
          venue_id: 'v1',
          label: 'Centenario',
          latitude: -34.89,
          longitude: -56.15,
          coordinate_precision: 'stadium',
        },
        {
          tournament_year: 1930,
          venue_id: 'v2',
          label: 'Pocitos',
          latitude: -34.91,
          longitude: -56.15,
          coordinate_precision: 'stadium',
        },
      ],
      legs: [
        {
          tournament_year: 1930,
          team_id: 'uruguay',
          team_name: 'Uruguay',
          leg_number: 1,
          from_match_id: 'a',
          to_match_id: 'b',
          from_latitude: -34.89,
          from_longitude: -56.15,
          to_latitude: -34.91,
          to_longitude: -56.15,
          distance_km: 2.2,
          is_projected: false,
        },
      ],
    }

    const { points, arcs } = buildAllTournamentMovementsGlobeData(movements)

    expect(points[0].id).toBe('1930-v1')
    expect(points[0].label).toBe('Centenario (1930)')
    expect(arcs[0].id).toBe('1930-uruguay-a-b')
    expect(arcs[0].tournamentYear).toBe(1930)
    expect(arcs[0].startLabel).toBe('Centenario')
  })
})
