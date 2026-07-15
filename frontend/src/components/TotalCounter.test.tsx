import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { TotalCounter } from '../components/TotalCounter'

describe('TotalCounter', () => {
  it('renders formatted total kilometres', () => {
    render(
      <TotalCounter totalKm={1234.5} completedKm={1200} projectedKm={34.5} isProjectedRoute />,
    )
    expect(screen.getByText('Approximate match-location travel')).toBeInTheDocument()
    expect(screen.getByText('1,235')).toBeInTheDocument()
  })
})
