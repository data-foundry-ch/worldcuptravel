import { test, expect } from '@playwright/test'

test('smoke: select tournament and team, see route data', async ({ page }) => {
  await page.goto('/')
  await page.waitForSelector('h1:has-text("World Cup Travel Atlas")', { timeout: 30000 })

  const yearSelect = page.locator('select').first()
  await yearSelect.selectOption({ label: /1930/ })
  const teamSelect = page.locator('select').nth(1)
  await teamSelect.waitFor({ state: 'visible' })
  await teamSelect.selectOption({ label: /Uruguay/i })

  await expect(page.locator('.total-counter__value')).not.toHaveText('0.0', { timeout: 15000 })
  await page.getByRole('button', { name: /Show itinerary/i }).click()
  await expect(page.locator('table tbody tr').first()).toBeVisible()
})
