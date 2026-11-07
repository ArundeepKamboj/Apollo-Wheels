const { test, expect } = require('../../frontend/node_modules/@playwright/test');
const fs = require('fs');
const path = require('path');
const root = path.resolve(__dirname, '../..');
const gateway = 'http://127.0.0.1:8100';
const auth = 'http://127.0.0.1:8104';
const contract = 'http://127.0.0.1:8101';
const pricing = 'http://127.0.0.1:8102';
const billing = 'http://127.0.0.1:8103';
const msaPath = path.join(root, 'samples/contracts/Northstar_Fleet_Services/northstar_msa_v1.pdf');
const invoicePath = path.join(root, 'samples/billing/Northstar_Fleet_Services/service/2026-02-01_service_inv-c-1001-feb-service.pdf');

async function human(request, username = 'testfinance', password = 'FinanceDemo!2026') {
  const response = await request.post(`${auth}/auth/token`, { form: { username, password } });
  expect(response.ok()).toBeTruthy();
  return { Authorization: `Bearer ${(await response.json()).access_token}` };
}
async function service(request, client_id, client_secret) {
  const response = await request.post(`${auth}/auth/service-token`, { form: { grant_type: 'client_credentials', client_id, client_secret } });
  expect(response.ok()).toBeTruthy();
  return { Authorization: `Bearer ${(await response.json()).access_token}` };
}

test('every API exposes Swagger UI and its OpenAPI schema', async ({ request }) => {
  for (const [base, title] of [
    [gateway, 'Apollo Wheels API Gateway'],
    [auth, 'Apollo Wheels Auth API'],
    [contract, 'Apollo Wheels Contract API'],
    [pricing, 'Apollo Wheels Pricing API'],
    [billing, 'Apollo Wheels Billing API'],
  ]) {
    const docs = await request.get(`${base}/docs`);
    expect(docs.ok(), `${base}/docs should respond`).toBeTruthy();
    expect(await docs.text()).toContain('Swagger UI');
    const schema = await request.get(`${base}/openapi.json`);
    expect(schema.ok(), `${base}/openapi.json should respond`).toBeTruthy();
    expect((await schema.json()).info.title).toBe(title);
  }
});

test('Auth, gateway, and scoped service accounts reject unauthenticated or unauthorized calls', async ({ request }) => {
  expect((await request.post(`${auth}/auth/token`, { form: { username: 'testfinance', password: 'wrong' } })).status()).toBe(401);
  expect((await request.get(`${gateway}/api/bootstrap`, { headers: { 'X-User-Role': 'finance', 'X-User-Id': 'finance.alex' } })).status()).toBe(401);
  expect((await request.get(`${contract}/api/bootstrap`)).status()).toBe(401);
  const finance = await human(request);
  expect((await request.get(`${gateway}/api/bootstrap`, { headers: finance })).ok()).toBeTruthy();
  expect((await request.post(`${auth}/auth/service-token`, { form: { grant_type: 'client_credentials', client_id: 'billing-service', client_secret: 'bad' } })).status()).toBe(401);
  const pricingAccount = await service(request, 'pricing-service', 'pricing-demo-secret');
  expect((await request.get(`${contract}/api/clients/C-1001`, { headers: pricingAccount })).ok()).toBeTruthy();
  expect((await request.get(`${pricing}/api/clients/C-1001/pricing`, { headers: pricingAccount })).status()).toBe(403);
  const billingAccount = await service(request, 'billing-service', 'billing-demo-secret');
  expect((await request.get(`${pricing}/api/clients/C-1001/pricing`, { headers: billingAccount })).ok()).toBeTruthy();
  expect((await request.get(`${billing}/api/audit/summary`, { headers: billingAccount })).status()).toBe(403);
});

test('Contract API enforces authenticated roles for upload, review, and Finance preferences', async ({ request }) => {
  const finance = await human(request);
  const structuring = await human(request, 'teststructurer', 'StructuringDemo!2026');
  expect((await request.get(`${contract}/`)).ok()).toBeTruthy();
  const bootstrap = await request.get(`${contract}/api/bootstrap`, { headers: finance });
  expect(bootstrap.ok()).toBeTruthy();
  expect((await bootstrap.json()).services).toHaveLength(13);
  expect((await (await request.get(`${contract}/api/clients/C-1001`, { headers: finance })).json()).id).toBe('C-1001');
  const agreements = await request.get(`${contract}/api/clients/C-1001/agreements`, { headers: finance });
  const agreement = (await agreements.json()).find(row => row.agreement_type === 'MSA');
  const originalPdf = await request.get(`${contract}/api/agreements/${agreement.id}/pdf`, { headers: finance });
  expect(originalPdf.headers()['content-type']).toContain('application/pdf');
  expect((await request.put(`${contract}/api/agreements/${agreement.id}/terms`, { headers: finance, data: { extracted: agreement.extracted } })).status()).toBe(403);
  expect((await request.put(`${contract}/api/agreements/${agreement.id}/terms`, { headers: structuring, data: { extracted: agreement.extracted } })).ok()).toBeTruthy();
  const upload = await request.post(`${contract}/api/clients/C-1001/agreements`, { headers: finance, multipart: { agreement_type: 'MSA', file: { name: 'sample_msa.pdf', mimeType: 'application/pdf', buffer: fs.readFileSync(msaPath) } } });
  expect(upload.ok()).toBeTruthy();
  expect((await upload.json()).extracted.services).toHaveLength(13);
  expect((await request.post(`${contract}/api/clients/C-1001/agreements`, { headers: finance, multipart: { agreement_type: 'MSA', file: { name: 'bad.txt', mimeType: 'text/plain', buffer: Buffer.from('bad') } } })).status()).toBe(400);
  expect((await request.put(`${contract}/api/clients/C-1001/invoice-history`, { headers: finance, data: { enabled: true } })).ok()).toBeTruthy();
  expect((await request.put(`${contract}/api/clients/C-1001/invoice-history`, { headers: structuring, data: { enabled: false } })).status()).toBe(403);
  expect((await request.get(`${contract}/api/clients/missing`, { headers: finance })).status()).toBe(404);
});

test('Pricing API uses authenticated Finance identity and enforces four-eyes activation', async ({ request }) => {
  const finance = await human(request);
  const secondFinance = await human(request, 'testfinance2', 'FinanceSecondDemo!2026');
  const structuring = await human(request, 'teststructurer', 'StructuringDemo!2026');
  const current = await request.get(`${pricing}/api/clients/C-1001/pricing`, { headers: finance });
  expect(current.ok()).toBeTruthy();
  const active = (await current.json()).components.filter(row => row.status === 'active');
  expect(active.length).toBeGreaterThan(0);
  const agreements = await (await request.get(`${contract}/api/clients/C-1001/agreements`, { headers: finance })).json();
  const body = { client_id: 'C-1001', agreement_ids: agreements.map(row => row.id), components: active.map(row => ({
    agreement_id: row.agreement_id, billing_stream: row.billing_stream, service_code: row.service_code,
    service_name: row.service_name, component_code: row.component_code, component_name: row.component_name,
    charge_type: row.charge_type, amount: row.amount, currency: row.currency, rate_unit: row.rate_unit,
    quantity: row.quantity, billing_frequency: row.billing_frequency, billing_day: row.billing_day,
    effective_from: row.effective_from, terms: JSON.parse(row.terms_json || '{}'),
  })) };
  expect((await request.post(`${pricing}/api/pricing/requests`, { headers: structuring, data: body })).status()).toBe(403);
  expect((await request.post(`${pricing}/api/pricing/requests`, { headers: finance, data: { ...body, components: [{ ...body.components[0], amount: -1 }] } })).status()).toBe(422);
  const submitted = await request.post(`${pricing}/api/pricing/requests`, { headers: finance, data: body });
  expect(submitted.ok()).toBeTruthy();
  const pending = await submitted.json();
  expect(pending.status).toBe('pending_approval');
  expect((await request.post(`${pricing}/api/pricing/requests/${pending.id}/approve`, { headers: finance })).status()).toBe(400);
  expect((await (await request.post(`${pricing}/api/pricing/requests/${pending.id}/approve`, { headers: secondFinance })).json()).status).toBe('active');
  expect((await request.post(`${pricing}/api/pricing/requests/${pending.id}/approve`, { headers: secondFinance })).status()).toBe(400);
});

test('Billing API authenticates PDF ingestion and audit/history integration calls', async ({ request }) => {
  const finance = await human(request);
  expect((await request.get(`${billing}/`)).ok()).toBeTruthy();
  const before = await request.get(`${billing}/api/clients/C-1001/billing-history?start=2026-02-01&end=2026-02-28`, { headers: finance });
  expect(before.ok()).toBeTruthy();
  const upload = await request.post(`${billing}/api/clients/C-1001/billing-documents`, { headers: finance, multipart: { file: { name: 'feb-service.pdf', mimeType: 'application/pdf', buffer: fs.readFileSync(invoicePath) } } });
  expect(upload.ok()).toBeTruthy();
  expect((await upload.json()).line_count).toBe(9);
  expect((await request.get(`${billing}/api/clients/C-1001/audit?start=2026-02-01&end=2026-02-28`, { headers: finance })).ok()).toBeTruthy();
  const summary = await request.get(`${billing}/api/audit/summary`, { headers: finance });
  expect((await summary.json()).clients).toHaveLength(2);
  const pdfs = (await (await request.get(`${billing}/api/clients/C-1001/pdfs`, { headers: finance })).json()).billing;
  const stored = await request.get(`${billing}${pdfs[0].url}`, { headers: finance });
  expect(stored.headers()['content-type']).toContain('application/pdf');
  expect((await request.get(`${billing}/api/files/missing`, { headers: finance })).status()).toBe(404);
});

test('gateway dispatches authenticated browser API requests to the owning service', async ({ request }) => {
  const finance = await human(request);
  const response = await request.get(`${gateway}/api/clients/C-1001/pricing`, { headers: finance });
  expect(response.ok()).toBeTruthy();
  expect((await response.json()).components.length).toBeGreaterThan(0);
  expect((await request.get(`${gateway}/api/audit/summary`, { headers: finance })).ok()).toBeTruthy();
});
