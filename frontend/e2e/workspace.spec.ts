import { expect, test } from '@playwright/test'

// These steps share the isolated workspace created by the first journey test.
test.describe.configure({ mode: 'serial' })

// Original synthetic resume fixture. Generates a real text-layer PDF and xref;
// the production pypdf extractor runs without mocking extraction or API responses.
function resumePdf(): Buffer {
  const lines = ['Demo Browser Candidate', 'Software Engineer', 'SUMMARY',
    'Builds Python database APIs.', 'SKILLS', 'Python, FastAPI, PostgreSQL',
    'PROJECTS', 'Evidence API | Python, FastAPI, PostgreSQL',
    '- Built transaction-safe API endpoints.', 'EDUCATION', 'Example University']
  const stream = `BT /F1 12 Tf 50 750 Td 16 TL ${lines.map((line) => `(${line}) Tj T*`).join(' ')} ET`
  const objects = ['<< /Type /Catalog /Pages 2 0 R >>', '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
    '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
    '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>', `<< /Length ${Buffer.byteLength(stream)} >>\nstream\n${stream}\nendstream`]
  let pdf = '%PDF-1.4\n'
  const offsets = [0]
  objects.forEach((object, index) => { offsets.push(Buffer.byteLength(pdf)); pdf += `${index + 1} 0 obj\n${object}\nendobj\n` })
  const xref = Buffer.byteLength(pdf)
  pdf += `xref\n0 6\n0000000000 65535 f \n${offsets.slice(1).map((offset) => `${String(offset).padStart(10, '0')} 00000 n \n`).join('')}`
  pdf += `trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF`
  return Buffer.from(pdf)
}

test('real PDF review → atomic import → job → report → edit → rerun → refresh', async ({ page, request }) => {
  await page.goto('/candidate')
  await page.getByLabel('PDF resume').setInputFiles({ name: 'browser-demo.pdf', mimeType: 'application/pdf', buffer: resumePdf() })
  await page.getByRole('button', { name: 'Create review draft' }).click()
  await expect(page.getByLabel('Full name', { exact: true })).toHaveValue('Demo Browser Candidate')
  // Extraction is only a draft, not a database write.
  expect(await (await request.get('/api/profiles')).json()).toHaveLength(0)
  await page.getByLabel('Full name', { exact: true }).fill('Reviewed Browser Candidate')
  await page.getByRole('button', { name: 'Confirm and create profile' }).click()
  await expect(page.getByText('Profile saved with 1 new and 0 updated project.')).toBeVisible()

  await page.getByRole('link', { name: '03 Jobs' }).click()
  await page.getByLabel('Company', { exact: true }).fill('Browser Demo Co')
  await page.getByLabel('Role title', { exact: true }).fill('Backend Engineer')
  await page.getByLabel('Job description', { exact: true }).fill('Build Python FastAPI PostgreSQL services. Docker preferred.')
  await page.getByRole('button', { name: 'Save job', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Backend Engineer', exact: true })).toBeVisible()
  await page.getByLabel('Application status').selectOption('applied')
  await expect(page.getByRole('status')).toHaveText('Application status updated.')
  await page.getByRole('button', { name: 'Analyze description' }).click()
  await expect(page.getByRole('heading', { name: 'Structured analysis' })).toBeVisible()
  await page.getByRole('link', { name: '04 Agent Match' }).click()
  await page.getByRole('button', { name: 'Run job-match agent' }).click()
  await expect(page.getByRole('heading', { name: 'Recommendation', exact: true })).toBeVisible()
  await page.getByText('Project · Evidence API · “Python”', { exact: true }).click()
  await expect(page.getByText('Built transaction-safe API endpoints.', { exact: true }).first()).toBeVisible()
  await page.reload()
  await expect(page.getByRole('heading', { name: 'Recommendation', exact: true })).toBeVisible()

  await page.getByRole('link', { name: '03 Jobs' }).click()
  await page.getByRole('button', { name: 'Edit job', exact: true }).click()
  await page.getByLabel('Edit job description').fill('Build Python FastAPI PostgreSQL and Java services.')
  await page.getByRole('button', { name: 'Save changes', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Analyze description' })).toBeVisible()
  await page.getByRole('link', { name: '04 Agent Match' }).click()
  await expect(page.getByText(/have changed since this report/)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Run job-match agent' })).toBeDisabled()
  await page.getByRole('link', { name: '03 Jobs' }).click()
  await page.getByRole('button', { name: 'Analyze description' }).click()
  await expect(page.getByRole('heading', { name: 'Structured analysis' })).toBeVisible()
  await page.getByRole('link', { name: '04 Agent Match' }).click()
  await page.getByRole('button', { name: 'Run job-match agent' }).click()
  await expect(page.getByText(/have changed since this report/)).toHaveCount(0)
  await expect(page.getByText('Java', { exact: true })).toBeVisible()
  await page.screenshot({ path: 'test-results/release-agent.png', fullPage: true })
})

test('search and status filters cover all API pages; UI pagination works', async ({ page, request }) => {
  // More than one backend page catches silent truncation at both 20 and 100.
  for (let index = 0; index < 102; index++) {
    const response = await request.post('/api/jobs', { data: {
      company_name: `Pagination Co ${index}`, title: 'Pagination role', description: 'Build Python APIs.',
    } })
    expect(response.status()).toBe(201)
  }
  await page.goto('/jobs')
  await page.getByLabel('Search saved jobs').fill('Pagination Co')
  await expect(page.getByText('Page 1 of 21 · 102 matching jobs')).toBeVisible()
  await expect(page.locator('.job-card')).toHaveCount(5)
  await page.getByRole('button', { name: 'Next page' }).click()
  await expect(page.getByText('Page 2 of 21 · 102 matching jobs')).toBeVisible()
  await page.getByLabel('Search saved jobs').fill('Browser Demo Co')
  await page.getByLabel('Filter by status').selectOption('applied')
  await expect(page.getByRole('heading', { name: 'Backend Engineer', exact: true })).toBeVisible()
  await page.getByLabel('Filter by status').selectOption('rejected')
  await expect(page.getByText('No jobs match these filters. Try another search or status.')).toBeVisible()
})

test('invalid PDF and failed real-agent mode have actionable errors', async ({ page }) => {
  await page.goto('/candidate')
  await page.getByLabel('PDF resume').setInputFiles({ name: 'bad.pdf', mimeType: 'application/pdf', buffer: Buffer.from('not a pdf') })
  await page.getByRole('button', { name: 'Create review draft' }).click()
  await expect(page.getByText('The uploaded file does not have a valid PDF header.')).toBeVisible()
  await page.goto('/agent')
  await page.getByLabel('Target job').selectOption({ label: 'Browser Demo Co · Backend Engineer' })
  await page.getByLabel('Execution mode').selectOption('openai')
  await page.getByRole('button', { name: 'Run job-match agent' }).click()
  await expect(page.getByRole('heading', { name: 'The run was saved, but it did not complete.' })).toBeVisible()
  await expect(page.getByText('OPENAI_API_KEY is not configured', { exact: true }).last()).toBeVisible()
  await page.reload()
  await expect(page.getByRole('heading', { name: 'The run was saved, but it did not complete.' })).toBeVisible()
})

test('network failure displays an error rather than a completed recommendation', async ({ page }) => {
  await page.route('**/api/agent-runs', (route) => route.request().method() === 'POST' ? route.abort() : route.continue())
  await page.goto('/agent')
  await page.getByLabel('Target job').selectOption({ label: 'Browser Demo Co · Backend Engineer' })
  await page.getByRole('button', { name: 'Run job-match agent' }).click()
  await expect(page.getByText(/Failed to fetch/)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Run job-match agent' })).toBeEnabled()
})

test('mobile navigation, filters, and source disclosure fit the viewport', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/agent')
  await expect(page.getByRole('heading', { name: 'Agent Match', exact: true })).toBeVisible()
  // History includes a failed run; choose the successful older run.
  await page.getByRole('button', { name: /Browser Demo Co · Backend Engineer.*completed/ }).first().click()
  await page.getByText('Project · Evidence API · “Python”', { exact: true }).click()
  await expect(page.getByText('Built transaction-safe API endpoints.', { exact: true }).first()).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
  await page.screenshot({ path: 'test-results/release-mobile.png', fullPage: true })
})
