import { useCallback, useEffect, useState } from 'react'

export interface UrlState {
  year: number | 'all' | null
  team: string | null
}

function readUrlState(): UrlState {
  const params = new URLSearchParams(window.location.search)
  const yearRaw = params.get('year')
  const year = yearRaw === 'all' ? 'all' : yearRaw ? Number(yearRaw) : null
  return {
    year: year === 'all' || Number.isFinite(year) ? year : null,
    team: year === 'all' ? null : params.get('team'),
  }
}

export function useUrlState(): [UrlState, (next: Partial<UrlState>) => void] {
  const [state, setLocalState] = useState<UrlState>(readUrlState)

  useEffect(() => {
    const onPop = () => setLocalState(readUrlState())
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])

  const setState = useCallback((next: Partial<UrlState>) => {
    const params = new URLSearchParams(window.location.search)
    if ('year' in next) {
      if (next.year) params.set('year', String(next.year))
      else params.delete('year')
      if (next.year === 'all') params.delete('team')
    }
    if ('team' in next) {
      if (next.team && params.get('year') !== 'all') params.set('team', next.team)
      else params.delete('team')
    }
    const qs = params.toString()
    const url = qs ? `${window.location.pathname}?${qs}` : window.location.pathname
    window.history.replaceState(null, '', url)
    setLocalState(readUrlState())
  }, [])

  return [state, setState]
}
