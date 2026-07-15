const EARTH_RADIUS_KM = 6371.0088

export function haversineKm(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number,
  radius = EARTH_RADIUS_KM,
): number {
  const toRad = (deg: number) => (deg * Math.PI) / 180
  const dLat = toRad(lat2 - lat1)
  const dLon = toRad(lon2 - lon1)
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2
  return radius * 2 * Math.asin(Math.sqrt(a))
}

export function formatKm(value: number): string {
  return value.toLocaleString('en-US', { maximumFractionDigits: 1, minimumFractionDigits: 1 })
}
