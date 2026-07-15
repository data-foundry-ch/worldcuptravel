import { describe, expect, it } from 'vitest'
import type { GlobeArc, GlobePoint } from './routeTransform'
import { buildTravelKpis } from './travelKpis'

const points: GlobePoint[] = [
  { id: 'a', lat: 1, lng: 1, label: 'Venue A', sequence: 1, isProjected: false },
  { id: 'b', lat: 2, lng: 2, label: 'Venue B', sequence: 2, isProjected: false },
  { id: 'b-repeat', lat: 2, lng: 2, label: 'Venue B', sequence: 3, isProjected: false },
  { id: 'c', lat: 3, lng: 3, label: 'Venue C', sequence: 4, isProjected: false },
]

const baseArc = {
  cumulativeKm: 0,
  isProjected: false,
  isComplete: true,
  duplicateIndex: 0,
  duplicateCount: 1,
  arcAltitude: 0.18,
}

const arcs: GlobeArc[] = [
  {
    ...baseArc,
    id: '1',
    teamName: 'Brazil',
    startLabel: 'Venue A',
    endLabel: 'Venue B',
    startLat: 1,
    startLng: 1,
    endLat: 2,
    endLng: 2,
    legNumber: 1,
    distanceKm: 428,
  },
  {
    ...baseArc,
    id: '2',
    teamName: 'Argentina',
    startLabel: 'Venue B',
    endLabel: 'Venue A',
    startLat: 2,
    startLng: 2,
    endLat: 1,
    endLng: 1,
    legNumber: 1,
    distanceKm: 512,
  },
  {
    ...baseArc,
    id: '3',
    teamName: 'France',
    startLabel: 'Venue B',
    endLabel: 'Venue C',
    startLat: 2,
    startLng: 2,
    endLat: 3,
    endLng: 3,
    legNumber: 1,
    distanceKm: 250,
  },
]

describe('buildTravelKpis', () => {
  it('builds travel KPIs from globe data', () => {
    const kpis = buildTravelKpis({
      totalKm: 1190,
      averageDivisor: 3,
      averageBasis: 'Per team',
      points,
      arcs,
    })

    expect(kpis.totalKm).toBe(1190)
    expect(kpis.averageKm).toBeCloseTo(396.67, 2)
    expect(kpis.averageLegKm).toBeCloseTo(396.67, 2)
    expect(kpis.locationCount).toBe(3)
    expect(kpis.longestSingleLeg).toEqual({
      label: 'Argentina: Venue B → Venue A',
      distanceKm: 512,
    })
    expect(kpis.mostRepeatedRoute).toEqual({
      label: 'Venue A ↔ Venue B',
      movementCount: 2,
    })
  })
})
