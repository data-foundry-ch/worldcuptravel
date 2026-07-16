import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react'
import type { GlobeArc, GlobePoint } from '../utils/routeTransform'

const Globe = lazy(() => import('react-globe.gl'))
const OPACITY = 0.65

function formatArcDistance(distanceKm: number | null): string | null {
  if (distanceKm == null) return null
  return `${distanceKm.toLocaleString('en-US', { maximumFractionDigits: 0 })} km`
}

function formatArcLabel(arc: GlobeArc): string {
  const distance = formatArcDistance(arc.distanceKm)
  const prefix = arc.tournamentYear ? `${arc.tournamentYear} · ` : ''
  const route = `${prefix}${arc.teamName}: ${arc.startLabel} → ${arc.endLabel}`
  return distance ? `${route} · ${distance}` : route
}

interface GlobeViewProps {
  points: GlobePoint[]
  arcs: GlobeArc[]
  onPointClick: (matchId: string) => void
  reducedMotion: boolean
}

export function GlobeView({
  points,
  arcs,
  onPointClick,
  reducedMotion,
}: GlobeViewProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const globeRef = useRef<{ pointOfView: (pov: object, ms?: number) => void } | null>(null)
  const [countries, setCountries] = useState<object[]>([])
  const [webglOk, setWebglOk] = useState(true)
  const [isTabVisible, setIsTabVisible] = useState(!document.hidden)
  const [hoverArc, setHoverArc] = useState<object | null>(null)
  const [dimensions, setDimensions] = useState({ width: window.innerWidth, height: window.innerHeight })

  useEffect(() => {
    try {
      const canvas = document.createElement('canvas')
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl')
      setWebglOk(!!gl)
    } catch {
      setWebglOk(false)
    }
  }, [])

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const updateDimensions = () => {
      const { width, height } = container.getBoundingClientRect()
      if (width > 0 && height > 0) {
        setDimensions({ width: Math.round(width), height: Math.round(height) })
      }
    }

    updateDimensions()
    const observer = new ResizeObserver(updateDimensions)
    observer.observe(container)
    window.addEventListener('resize', updateDimensions)

    return () => {
      observer.disconnect()
      window.removeEventListener('resize', updateDimensions)
    }
  }, [])

  useEffect(() => {
    fetch('/countries.geojson')
      .then((r) => r.json())
      .then((data) => setCountries((data as { features: object[] }).features))
      .catch(() => setCountries([]))
  }, [])

  useEffect(() => {
    const onVisibilityChange = () => setIsTabVisible(!document.hidden)
    document.addEventListener('visibilitychange', onVisibilityChange)
    return () => document.removeEventListener('visibilitychange', onVisibilityChange)
  }, [])

  const focusRoute = useCallback(() => {
    if (!globeRef.current || !points.length) return
    const lats = points.map((p) => p.lat)
    const lngs = points.map((p) => p.lng)
    const lat = (Math.min(...lats) + Math.max(...lats)) / 2
    const lng = (Math.min(...lngs) + Math.max(...lngs)) / 2
    const span = Math.max(Math.max(...lats) - Math.min(...lats), Math.max(...lngs) - Math.min(...lngs))
    const altitude = Math.min(2.8, Math.max(1.2, 2.5 - span * 0.3))
    globeRef.current.pointOfView({ lat, lng, altitude }, reducedMotion ? 0 : 1200)
  }, [points, reducedMotion])

  useEffect(() => {
    focusRoute()
  }, [focusRoute, points])

  if (!webglOk) {
    return (
      <div className="globe-fallback" ref={containerRef}>
        <p>3D globe unavailable (WebGL not supported). Use the itinerary table below.</p>
      </div>
    )
  }

  const animateArcs = arcs.length > 0 && !reducedMotion && isTabVisible

  return (
    <div className="globe-view" ref={containerRef}>
      <Suspense fallback={<div className="globe-loading">Loading globe…</div>}>
        <Globe
          ref={globeRef as never}
          width={dimensions.width}
          height={dimensions.height}
          backgroundColor="rgba(0,0,0,0)"
          globeImageUrl="/earth_at_night.jpg"
          bumpImageUrl={null}
          showAtmosphere
          atmosphereColor="rgba(120,160,220,0.25)"
          atmosphereAltitude={0.12}
          polygonsData={countries}
          polygonCapColor={() => 'rgba(40, 48, 58, 0.55)'}
          polygonSideColor={() => 'rgba(20, 24, 30, 0.2)'}
          polygonStrokeColor={() => 'rgba(100, 120, 140, 0.35)'}
          polygonAltitude={0.003}
          pointsData={points}
          pointLat="lat"
          pointLng="lng"
          pointAltitude={0.003}
          pointRadius={0.18}
          pointColor={(d: object) => {
            const p = d as GlobePoint
            return p.isProjected ? 'rgba(120, 200, 255, 0.9)' : 'rgba(198, 159, 73, 0.95)'
          }}
          pointLabel={(d: object) => (d as GlobePoint).label}
          onPointClick={(d: object) => onPointClick((d as GlobePoint).id)}
          arcsData={arcs}
          arcStartLat="startLat"
          arcStartLng="startLng"
          arcEndLat="endLat"
          arcEndLng="endLng"
          arcAltitude={(d: object) => (d as GlobeArc).arcAltitude}
          arcLabel={(d: object) => formatArcLabel(d as GlobeArc)}
          arcColor={(d: object) => {
            const op = !hoverArc ? OPACITY : d === hoverArc ? 0.9 : OPACITY / 4
            return [`rgba(198, 159, 73, ${op})`, `rgba(54, 40, 17, ${op})`]
          }}
          arcStroke={0.2}
          arcDashLength={animateArcs ? 0.80 : 1}
          arcDashGap={0.05}
          arcDashInitialGap={(d: object) => ((d as GlobeArc).legNumber % 8) * 0.08}
          arcDashAnimateTime={animateArcs ? 7500 : 0}
          arcsTransitionDuration={0}
          onArcHover={(d: object | null) => setHoverArc(d)}
          animateIn={!reducedMotion}
        />
      </Suspense>
    </div>
  )
}
