import { describe, expect, it } from 'vitest'
import { haversineKm } from '../utils/haversine'

describe('haversineKm', () => {
  it('returns zero for identical points', () => {
    expect(haversineKm(0, 0, 0, 0)).toBeCloseTo(0, 5)
  })

  it('matches known Paris-London distance', () => {
    const km = haversineKm(48.8566, 2.3522, 51.5074, -0.1278)
    expect(km).toBeGreaterThan(340)
    expect(km).toBeLessThan(360)
  })
})
