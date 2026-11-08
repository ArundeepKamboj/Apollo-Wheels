const { test, expect } = require('@playwright/test');
const path = require('path');

const root = path.resolve(__dirname, '../..');
const sampleInvoice = path.join(root, 'samples/billing/Northstar_Fleet_Services/service/2026-02-01_service_inv-c-1001-feb-service.pdf');
const sampleMsa = path.join(root, 'samples/test_uploads/Test_Client/test_client_msa_v1.pdf');
const sampleMla = path.join(root, 'samples/test_uploads/Test_Client/test_client_mla_v1.pdf');

async function signIn(page, username = 'testfinance', password = 'FinanceDemo!2026') {
  if (await page.locator('#login-form').count() === 0) await page.locator('#logout').click();
  await page.locator('#login-username').fill(username);
  await page.locator('#login-password').fill(password);
  await page.locator('#login-form button').click();
}

async function openWorkspace(page) {
  await page.goto('/');
  if (await page.locator('#login-form').count()) await signIn(page);
  await expect(page.getByRole('heading', { name: 'Contract & billing control' })).toBeVisible();
}

test('login is required and displays the authenticated Finance user', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Sign in to Wheels' })).toBeVisible();
  await signIn(page);
  await expect(page.locator('#user-label')).toContainText('Finance · Alex');
  await expect(page.getByRole('heading', { name: 'Contract & billing control' })).toBeVisible();
});

test('overview shows the internal demo and all workflow navigation', async ({ page }) => {
  await openWorkspace(page);
  await expect(page.locator('#main')).toContainText('Apollo Wheels - Internal workspace');
  await expect(page.locator('.nav')).toHaveCount(4);
  await expect(page.getByText('13 services', { exact: true })).toBeVisible();
  await expect(page.locator('.audit-stat strong').first()).toHaveText('Northstar Fleet Services');
});

test('contract workspace shows source and role-specific editing after login', async ({ page }) => {
  await openWorkspace(page);
  await page.locator('.nav[data-page="contracts"]').click();
  await expect(page.getByRole('heading', { name: 'Source document' })).toBeVisible();
  await expect(page.locator('#existing-client-picker')).toHaveValue('');
  await expect(page.locator('.pdf-page')).toHaveCount(0);
  await expect(page.locator('#terms-editor')).toContainText('Select an existing client');
  await expect(page.locator('#download-agreement')).toHaveCount(0);
  await expect(page.locator('#agreement-upload')).toHaveCount(0);
  let unsolicitedDownload = false;
  page.on('download', () => { unsolicitedDownload = true; });
  await page.locator('#existing-client-picker').selectOption('C-1001');
  await expect(page.locator('#existing-agreement-type')).toHaveValue('');
  await expect(page.locator('#fetch-agreement')).toBeDisabled();
  await page.locator('#existing-agreement-type').selectOption('MSA');
  await expect(page.locator('#fetch-agreement')).toBeEnabled();
  await page.locator('#fetch-agreement').click();
  await expect(page.locator('#pdf-viewer')).toHaveAttribute('data-state', 'ready');
  const pageCount = Number(await page.locator('#pdf-viewer').getAttribute('data-page-count'));
  await expect(page.locator('.pdf-page')).toHaveCount(pageCount);
  await expect(page.locator('.pdf-page canvas').first()).toBeVisible();
  const canvasSize = await page.locator('.pdf-page canvas').first().evaluate(canvas => ({ width: canvas.width, height: canvas.height }));
  expect(canvasSize.width).toBeGreaterThan(0);
  expect(canvasSize.height).toBeGreaterThan(0);
  await expect(page.locator('#terms-editor')).toContainText('Fuel');
  await page.waitForTimeout(300);
  expect(unsolicitedDownload).toBe(false);
  const download = page.waitForEvent('download');
  await page.locator('#download-agreement').click();
  expect((await download).suggestedFilename()).toContain('msa');
  await expect(page.locator('#save-terms')).toBeDisabled();
  await signIn(page, 'teststructurer', 'StructuringDemo!2026');
  // Navigate away then back so the picker resets (go() resets only when arriving
  // from a different page).
  await page.locator('.nav[data-page="overview"]').click();
  await page.locator('.nav[data-page="contracts"]').click();
  await expect(page.locator('#existing-client-picker')).toHaveValue('');
  await page.locator('#existing-client-picker').selectOption('C-1001');
  await page.locator('#existing-agreement-type').selectOption('MSA');
  await page.locator('#fetch-agreement').click();
  await expect(page.locator('#save-terms')).toBeEnabled();
  await expect(page.locator('#terms-editor')).toContainText('Evidence - page');
  await expect(page.locator('#terms-editor')).toContainText('Evidence - page');
  const panelHeights = await page.locator('.contract-panel').evaluateAll(nodes => nodes.map(node => node.getBoundingClientRect().height));
  expect(Math.abs(panelHeights[0] - panelHeights[1])).toBeLessThan(2);
  await page.setViewportSize({ width: 640, height: 780 });
  const mobilePanelHeights = await page.locator('.contract-panel').evaluateAll(nodes => nodes.map(node => node.getBoundingClientRect().height));
  expect(Math.abs(mobilePanelHeights[0] - mobilePanelHeights[1])).toBeLessThan(2);
});

test('agreement upload identifies MSA or MLA and displays extracted fields', async ({ page }) => {
  await openWorkspace(page);
  await signIn(page, 'teststructurer', 'StructuringDemo!2026');
  await page.locator('.nav[data-page="contracts"]').click();
  await page.locator('#tab-upload').click();
  await expect(page.locator('#agreement-upload')).toBeVisible();
  await expect(page.locator('#agreement-upload input[type="file"]')).toBeEnabled();

  for (const [file, type, field] of [
    [sampleMsa, 'MSA', 'Fuel'],
    [sampleMla, 'MLA', 'Lease term'],
  ]) {
    await page.locator('#agreement-upload input[type="file"]').setInputFiles(file);
    await page.locator('#agreement-upload button').click();
    await expect(page.locator('#toast')).toContainText(`${type} identified`);
    // The uploaded PDF must render on the left even though it is a draft
    // (selectedAgreement stays null; the draft lives in uploadedAgreement).
    await expect(page.locator('#pdf-viewer')).toHaveAttribute('data-state', 'ready');
    await expect(page.locator('.pdf-page').first()).toBeVisible();
    // Text layer spans are rendered by PDF.js; check that the first non-empty span is present.
    await expect(page.locator('.pdf-text-layer span').filter({ hasText: /.+/ }).first()).toBeVisible();
    await expect(page.locator('#terms-editor')).toContainText(type);
    await expect(page.locator('#terms-editor')).toContainText(field);
    if (type === 'MSA') {
      await page.locator('.service-edit').first().hover();
      await expect(page.locator('.pdf-text-highlight').first()).toBeVisible();
    }
  }
});

test('Finance pricing request requires a different authenticated Finance approver', async ({ page }) => {
  await openWorkspace(page);
  await page.locator('.nav[data-page="pricing"]').click();
  await page.locator('#load-contract-pricing').click();
  await expect(page.locator('.pricing-row').first()).toBeVisible();
  await page.locator('#submit-pricing').click();
  await expect(page.locator('#toast')).toContainText('waiting for second approval');
  await expect(page.locator('.approve-btn').first()).toBeDisabled();
  await signIn(page, 'testfinance2', 'FinanceSecondDemo!2026');
  await page.locator('.nav[data-page="pricing"]').click();
  const approve = page.locator('.approve-btn').first();
  await expect(approve).toBeEnabled();
  await approve.click();
  await expect(page.locator('#toast')).toContainText('now active');
});

test('billing workspace ingests PDF, shows line history, and filters by period', async ({ page }) => {
  await openWorkspace(page);
  await page.locator('.nav[data-page="billing"]').click();
  await page.locator('input[type="file"]').setInputFiles(sampleInvoice);
  await page.locator('#billing-upload button').click();
  await expect(page.locator('#toast')).toContainText('Ingested 9 billing lines');
  await expect(page.locator('body')).toContainText('INV-C-1001-FEB-SERVICE');
  await expect(page.locator('body')).toContainText('Billed rate differs from active pricing');
  await page.locator('#history-start').fill('2026-02-01');
  await page.locator('#history-end').fill('2026-02-28');
  await page.locator('#filter-history').click();
  await expect(page.locator('body')).toContainText('History filters applied');
});

test('Finance controls invoice-history preference and Structuring cannot change it', async ({ page }) => {
  await openWorkspace(page);
  await page.locator('.nav[data-page="billing"]').click();
  await expect(page.locator('#history-toggle')).toBeEnabled();
  await signIn(page, 'teststructurer', 'StructuringDemo!2026');
  await page.locator('.nav[data-page="billing"]').click();
  await expect(page.locator('#history-toggle')).toBeDisabled();
});

test('overview renders a recoverable message when an API request fails', async ({ page }) => {
  await page.route('**/api/bootstrap', route => route.abort());
  await page.goto('/');
  await signIn(page);
  await expect(page.locator('#main')).toContainText(/failed|network|fetch/i);
});
