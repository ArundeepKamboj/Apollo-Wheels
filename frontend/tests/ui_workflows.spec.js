const { test, expect } = require("@playwright/test");
const path = require("path");

const root = path.resolve(__dirname, "../..");
const sampleInvoice = path.join(
  root,
  "samples/billing/Northstar_Fleet_Services/service/2026-02-01_service_inv-c-1001-feb-service.pdf",
);
const sampleMsa = path.join(
  root,
  "samples/contracts/Northstar_Fleet_Services/northstar_msa_v1.pdf",
);
const sampleMla = path.join(
  root,
  "samples/contracts/Blue_River_Logistics/blueriver_mla_v1.pdf",
);
const sampleNewClientMsa = path.join(
  root,
  "samples/test_uploads/Test_Client/test_client_msa_v1.pdf",
);

async function signIn(
  page,
  username = "testfinance",
  password = "FinanceDemo!2026",
) {
  if ((await page.locator("#login-form").count()) === 0)
    await page.locator("#logout").click();
  await page.locator("#login-username").fill(username);
  await page.locator("#login-password").fill(password);
  await page.locator("#login-form button").click();
}

async function openWorkspace(page) {
  await page.goto("/");
  if (await page.locator("#login-form").count()) await signIn(page);
  await expect(
    page.getByRole("heading", { name: "Contract & billing control" }),
  ).toBeVisible();
}

test("login is required and displays the authenticated Finance user", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Sign in to Wheels" }),
  ).toBeVisible();
  await signIn(page);
  await expect(page.locator("#user-label")).toContainText("Finance · Alex");
  await expect(
    page.getByRole("heading", { name: "Contract & billing control" }),
  ).toBeVisible();
});

test("refresh preserves the current page but sign-in starts at Overview", async ({
  page,
}) => {
  await page.goto("/");
  await signIn(page);
  await expect(
    page.getByRole("heading", { name: "Contract & billing control" }),
  ).toBeVisible();

  await page.locator('.nav[data-page="pricing"]').click();
  await expect(
    page.getByRole("heading", { name: "Pricing setup & approval" }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Pricing setup & approval" }),
  ).toBeVisible();

  await signIn(page);
  await expect(
    page.getByRole("heading", { name: "Contract & billing control" }),
  ).toBeVisible();
});

test("overview shows workspace content without demo data labels", async ({
  page,
}) => {
  await openWorkspace(page);
  await expect(page.locator("#main")).toContainText(
    "Apollo Wheels - Internal workspace",
  );
  await expect(page.locator("#main")).toContainText("Clients");
  await expect(page.locator("#main")).not.toContainText(/demo|synthetic/i);
  await expect(page.locator(".sidebar-bottom")).toContainText(
    "Workspace active",
  );
  await expect(page.locator(".sidebar-bottom")).not.toContainText(
    /demo|synthetic/i,
  );
  await expect(page.locator(".internal-badge")).toHaveCount(0);
  await expect(page.locator(".nav")).toHaveCount(4);
  await expect(page.locator('.nav[data-page="contracts"]')).toContainText(
    "Contract",
  );
  await expect(page.locator('.nav[data-page="pricing"]')).toContainText(
    "Pricing",
  );
  await expect(page.getByText("13 services", { exact: true })).toBeVisible();
  await expect(page.locator(".audit-stat strong").first()).toHaveText(
    "Northstar Fleet Services",
  );
});

test("Structuring users only see Overview and Contract sections", async ({
  page,
}) => {
  await page.goto("/");
  await signIn(page, "teststructurer", "StructuringDemo!2026");

  await expect(page.locator('.nav[data-page="overview"]')).toBeVisible();
  await expect(page.locator('.nav[data-page="contracts"]')).toBeVisible();
  await expect(page.locator('.nav[data-page="pricing"]')).toBeHidden();
  await expect(page.locator('.nav[data-page="billing"]')).toBeHidden();
  await expect(page.locator("#main")).not.toContainText("Pending approvals");
  await expect(page.locator("#main")).not.toContainText("Billing audit");
  await expect(page.locator("#main")).not.toContainText("Client audit summary");

  await page.locator('.nav[data-page="contracts"]').click();
  await expect(page.locator("#tab-existing")).toHaveText("Existing Aggrement");
  await expect(page.locator("#tab-upload")).toHaveText("Upload Agreement");
  await page.evaluate(() => go("pricing"));
  await expect(
    page.getByRole("heading", { name: "Source document" }),
  ).toBeVisible();
});

test("contract workspace shows source and role-specific editing after login", async ({
  page,
}) => {
  await openWorkspace(page);
  await page.locator('.nav[data-page="contracts"]').click();
  await expect(
    page.getByRole("heading", { name: "Source document" }),
  ).toBeVisible();
  await expect(page.locator("#existing-client-picker")).toHaveValue("");
  await expect(page.locator("#existing-client-picker option")).toHaveCount(3);
  await expect(page.locator("#existing-client-picker")).not.toContainText("Test Client");
  await expect(page.locator("#existing-client-picker")).toContainText("Northstar Fleet Services");
  await expect(page.locator("#existing-client-picker")).toContainText("Blue River Logistics");
  await expect(page.locator(".pdf-page")).toHaveCount(0);
  await expect(page.locator("#terms-editor")).toContainText(
    "Select an existing client",
  );
  await expect(page.locator("#download-agreement")).toHaveCount(0);
  await expect(page.locator("#agreement-upload")).toHaveCount(0);
  let unsolicitedDownload = false;
  page.on("download", () => {
    unsolicitedDownload = true;
  });
  await page.locator("#existing-client-picker").selectOption("C-1001");
  await expect(page.locator("#existing-agreement-type")).toHaveValue("");
  await expect(page.locator("#fetch-agreement")).toBeDisabled();
  await page.locator("#existing-agreement-type").selectOption("MSA");
  await expect(page.locator("#fetch-agreement")).toBeEnabled();
  await page.locator("#fetch-agreement").click();
  await expect(page.locator("#pdf-viewer")).toHaveAttribute(
    "data-state",
    "ready",
  );
  const pageCount = Number(
    await page.locator("#pdf-viewer").getAttribute("data-page-count"),
  );
  await expect(page.locator(".pdf-page")).toHaveCount(pageCount);
  await expect(page.locator(".pdf-page canvas").first()).toBeVisible();
  const canvasSize = await page
    .locator(".pdf-page canvas")
    .first()
    .evaluate((canvas) => ({ width: canvas.width, height: canvas.height }));
  expect(canvasSize.width).toBeGreaterThan(0);
  expect(canvasSize.height).toBeGreaterThan(0);
  await expect(page.locator("#terms-editor")).toContainText("Fuel");
  await expect(page.locator("#terms-editor")).toContainText(
    "Legal entity name",
  );
  await expect(page.locator("#terms-editor")).toContainText(
    "Northstar Fleet Services, LLC",
  );
  await page.waitForTimeout(300);
  expect(unsolicitedDownload).toBe(false);
  const download = page.waitForEvent("download");
  await page.locator("#download-agreement").click();
  expect((await download).suggestedFilename()).toContain("msa");
  await expect(page.locator("#save-terms")).toBeDisabled();
  await signIn(page, "teststructurer", "StructuringDemo!2026");
  // Navigate away then back so the picker resets (go() resets only when arriving
  // from a different page).
  await page.locator('.nav[data-page="overview"]').click();
  await page.locator('.nav[data-page="contracts"]').click();
  await expect(page.locator("#existing-client-picker")).toHaveValue("");
  await page.locator("#existing-client-picker").selectOption("C-1001");
  await page.locator("#existing-agreement-type").selectOption("MSA");
  await page.locator("#fetch-agreement").click();
  await expect(page.locator("#save-terms")).toBeEnabled();
  await expect(page.locator("#terms-editor")).toContainText("Evidence - page");
  await expect(page.locator("#terms-editor")).toContainText("Evidence - page");
  const panelHeights = await page
    .locator(".contract-panel")
    .evaluateAll((nodes) =>
      nodes.map((node) => node.getBoundingClientRect().height),
    );
  expect(Math.abs(panelHeights[0] - panelHeights[1])).toBeLessThan(2);
  await page.setViewportSize({ width: 640, height: 780 });
  const mobilePanelHeights = await page
    .locator(".contract-panel")
    .evaluateAll((nodes) =>
      nodes.map((node) => node.getBoundingClientRect().height),
    );
  expect(Math.abs(mobilePanelHeights[0] - mobilePanelHeights[1])).toBeLessThan(
    2,
  );
});

test("contract tabs retain the selected agreement and preview close does not reload it", async ({
  page,
}) => {
  await openWorkspace(page);
  await page.locator('.nav[data-page="contracts"]').click();
  await page.locator("#existing-client-picker").selectOption("C-1001");
  await page.locator("#existing-agreement-type").selectOption("MSA");
  await page.locator("#fetch-agreement").click();
  await expect(page.locator("#pdf-viewer")).toHaveAttribute(
    "data-state",
    "ready",
  );
  await expect(page.locator("#terms-editor")).toContainText(
    "Northstar Fleet Services, LLC",
  );

  await page.locator("#tab-upload").click();
  await expect(page.locator("#agreement-upload")).toBeVisible();
  await page.locator("#tab-existing").click();
  await expect(page.locator("#existing-client-picker")).toHaveValue("C-1001");
  await expect(page.locator("#existing-agreement-type")).toHaveValue("MSA");
  await expect(page.locator("#terms-editor")).toContainText(
    "Northstar Fleet Services, LLC",
  );
  await expect(page.locator("#pdf-viewer")).toHaveAttribute(
    "data-state",
    "ready",
  );

  const agreementAndPdfRequests = [];
  page.on("request", (request) => {
    if (
      request.url().includes("/api/clients/C-1001/agreements?type=MSA") ||
      (request.url().includes("/api/agreements/") &&
        request.url().endsWith("/pdf"))
    ) {
      agreementAndPdfRequests.push(request.url());
    }
  });
  const requestsBeforePreview = agreementAndPdfRequests.length;
  await page.locator("#preview-billing").click();
  await expect(
    page.getByRole("heading", { name: "Forecast Billing Preview" }),
  ).toBeVisible();
  await page.locator("#close-preview-modal-btn").click();
  await expect(page.locator(".modal-overlay")).toHaveCount(0);
  await expect(page.locator("#pdf-viewer")).toHaveAttribute(
    "data-state",
    "ready",
  );
  await expect(page.locator("#terms-editor")).toContainText(
    "Northstar Fleet Services, LLC",
  );
  expect(agreementAndPdfRequests).toHaveLength(requestsBeforePreview);
});

test("Structuring saves an MLA rate and refreshes evidence against the new PDF", async ({
  page,
}) => {
  await openWorkspace(page);
  await signIn(page, "teststructurer", "StructuringDemo!2026");
  await page.locator('.nav[data-page="contracts"]').click();
  await page.locator("#existing-client-picker").selectOption("C-1001");
  await page.locator("#existing-agreement-type").selectOption("MLA");
  await page.locator("#fetch-agreement").click();
  const rate = page.locator('[data-lease-field="0|contract_amount"]');
  const updatedRate = Number(await rate.inputValue()) + 0.5;
  const displayedRate = new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 2,
  }).format(updatedRate);
  page.on("dialog", (dialog) => dialog.accept("Refresh MLA rate evidence"));
  await rate.fill(String(updatedRate));
  await page.locator("#save-terms").click();
  await expect(page.locator("#toast")).toContainText(
    "New version saved with audit comment",
  );
  await expect(page.locator("#pdf-viewer")).toHaveAttribute(
    "data-state",
    "ready",
  );
  await expect(
    page.locator('[data-lease-field="0|contract_amount"]'),
  ).toHaveValue(String(updatedRate));
  await expect(page.locator("#terms-editor")).toContainText(displayedRate);
  await page.locator('[data-lease-field="0|contract_amount"]').hover();
  await expect(page.locator(".pdf-text-highlight").first()).toBeVisible();
});

test("agreement upload identifies MSA or MLA and displays extracted fields", async ({
  page,
}) => {
  await openWorkspace(page);
  await signIn(page, "teststructurer", "StructuringDemo!2026");
  await page.locator('.nav[data-page="contracts"]').click();
  await page.locator("#tab-upload").click();
  await expect(page.locator("#agreement-upload")).toBeVisible();
  await expect(
    page.locator('#agreement-upload input[type="file"]'),
  ).toBeEnabled();

  for (const [file, type, field] of [
    [sampleMsa, "MSA", "Fuel"],
    [sampleMla, "MLA", "Lease term"],
  ]) {
    await page
      .locator('#agreement-upload input[type="file"]')
      .setInputFiles(file);
    await page.locator("#agreement-upload button").click();
    await expect(page.locator("#toast")).toContainText(`${type} identified`);
    // The uploaded PDF must render on the left even though it is a draft
    // (selectedAgreement stays null; the draft lives in uploadedAgreement).
    await expect(page.locator("#pdf-viewer")).toHaveAttribute(
      "data-state",
      "ready",
    );
    await expect(page.locator(".pdf-page").first()).toBeVisible();
    // Text layer spans are rendered by PDF.js; check that the first non-empty span is present.
    await expect(
      page.locator(".pdf-text-layer span").filter({ hasText: /.+/ }).first(),
    ).toBeVisible();
    await expect(page.locator("#terms-editor")).toContainText(type);
    await expect(page.locator("#terms-editor")).toContainText(field);
    if (type === "MSA") {
      await page.locator(".service-edit").first().hover();
      await expect(page.locator(".pdf-text-highlight").first()).toBeVisible();
    }
  }
});

test("agreement upload creates a new client when saving its draft", async ({
  page,
}) => {
  await openWorkspace(page);
  await signIn(page, "teststructurer", "StructuringDemo!2026");
  await page.locator('.nav[data-page="contracts"]').click();
  await page.locator("#tab-upload").click();
  await page
    .locator('#agreement-upload input[type="file"]')
    .setInputFiles(sampleNewClientMsa);
  await page.locator("#agreement-upload button").click();

  await expect(page.locator("#toast")).toContainText("MSA identified");
  await expect(page.locator("#terms-editor")).toContainText("Test Client");
  await expect(page.locator("#terms-editor")).toContainText("Fuel");
  await page.locator("#save-draft-btn").click();

  await expect(page.locator("#toast")).toContainText("Draft saved in system");
  await expect(page.locator("#terms-editor")).toContainText("Test Client");
  await expect(page.locator(".contract-panel .tag.good")).toContainText(
    "review",
  );
});

test("Finance pricing request requires a different authenticated Finance approver", async ({
  page,
}) => {
  await openWorkspace(page);
  await page.locator('.nav[data-page="pricing"]').click();
  await page.locator("#load-contract-pricing").click();
  await expect(page.locator(".pricing-row").first()).toBeVisible();
  await page.locator("#submit-pricing").click();
  await expect(page.locator("#toast")).toContainText(
    "waiting for second approval",
  );
  const review = page.locator(".review-pricing-btn").first();
  await review.click();
  const ownReview = page.getByRole("dialog", {
    name: "Pricing approval details",
  });
  await expect(ownReview).toContainText("Fuel");
  await expect(ownReview).toContainText("Pricing terms");
  await expect(ownReview).toContainText(/\$\d+\.\d{2}/);
  await expect(
    ownReview.getByRole("button", {
      name: "Approve and activate this version",
    }),
  ).toBeDisabled();
  await ownReview.getByRole("button", { name: "Close", exact: true }).click();
  await signIn(page, "testfinance2", "FinanceSecondDemo!2026");
  await page.locator('.nav[data-page="pricing"]').click();
  await page.locator(".review-pricing-btn").first().click();
  const secondReview = page.getByRole("dialog", {
    name: "Pricing approval details",
  });
  await expect(secondReview).toContainText("Fuel");
  await expect(secondReview).toContainText("Pricing terms");
  await expect(secondReview).toContainText(/\$\d+\.\d{2}/);
  const approve = secondReview.getByRole("button", {
    name: "Approve and activate this version",
  });
  await expect(approve).toBeEnabled();
  await approve.click();
  await expect(page.locator("#toast")).toContainText("now active");
});

test("Finance can edit service and component names before submitting pricing", async ({
  page,
}) => {
  await openWorkspace(page);
  await page.locator('.nav[data-page="pricing"]').click();
  await page.locator("#add-component").click();

  await page.locator('[data-field="service_name"]').fill("Roadside support");
  await page.locator('[data-field="component_name"]').fill("Per event fee");

  let submittedRequest;
  await page.route("**/api/pricing/requests", async (route) => {
    submittedRequest = route.request().postDataJSON();
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({
        id: "pricing-edit-test",
        client_id: "C-1001",
        version: 99,
        status: "pending_approval",
      }),
    });
  });
  await page.locator("#submit-pricing").click();

  await expect(page.locator("#toast")).toContainText(
    "waiting for second approval",
  );
  expect(submittedRequest.components[0]).toMatchObject({
    service_name: "Roadside support",
    service_code: "ROADSIDE_SUPPORT",
    component_name: "Per event fee",
    component_code: "per_event_fee",
  });
});

test("billing audit shows comparison, hides history, and rejects duplicate invoices", async ({
  page,
}) => {
  let auditRequest;
  let combinedRequest;
  await page.route("**/api/clients/*/audit**", async (route) => {
    auditRequest = new URL(route.request().url());
    await route.continue();
  });
  await page.route("**/api/clients/*/billing-combined**", async (route) => {
    combinedRequest = new URL(route.request().url());
    await route.continue();
  });
  await openWorkspace(page);
  await page.locator('.nav[data-page="billing"]').click();
  await expect(page.locator("#audit-view")).toBeVisible();
  await expect(page.locator("#history-view")).toBeHidden();
  const previousMonth = await page.evaluate(() => {
    const today = new Date();
    const start = new Date(today.getFullYear(), today.getMonth() - 1, 1);
    const end = new Date(today.getFullYear(), today.getMonth(), 0);
    const formatDate = (date) =>
      `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
    return { start: formatDate(start), end: formatDate(end) };
  });
  await expect(page.locator("#audit-start")).toHaveValue(previousMonth.start);
  await expect(page.locator("#audit-end")).toHaveValue(previousMonth.end);
  expect(auditRequest.searchParams.get("start")).toBe(previousMonth.start);
  expect(auditRequest.searchParams.get("end")).toBe(previousMonth.end);
  await page.locator("#billing-history-tab").click();
  await expect(page.locator("#history-view")).toBeVisible();
  await expect(page.locator("#audit-view")).toBeHidden();
  await expect(page.locator("#combined-panel")).toContainText(
    "Bill history (service + lease)",
  );
  await expect(page.locator("#combined-start")).toHaveValue(previousMonth.start);
  await expect(page.locator("#combined-end")).toHaveValue(previousMonth.end);
  expect(combinedRequest.searchParams.get("start")).toBe(previousMonth.start);
  expect(combinedRequest.searchParams.get("end")).toBe(previousMonth.end);
  await page.locator("#billing-audit-tab").click();
  await expect(page.locator("#audit-view")).toBeVisible();
  await page.locator('input[type="file"]').setInputFiles(sampleInvoice);
  await page.locator("#billing-upload button").click();
  await expect(page.locator("#toast")).toContainText("has already been uploaded");
});

test("workspace sidebar stays visible while scrolling on desktop and mobile", async ({
  page,
}) => {
  await openWorkspace(page);
  await page.locator("#main").evaluate((main) => {
    main.style.minHeight = "1800px";
  });
  for (const viewport of [
    { width: 1280, height: 720 },
    { width: 390, height: 844 },
  ]) {
    await page.setViewportSize(viewport);
    await page.evaluate(() => window.scrollTo(0, 600));
    const positions = await page.evaluate(() => ({
      topbarBottom: document.querySelector(".topbar").getBoundingClientRect().bottom,
      sidebarTop: document.querySelector(".sidebar").getBoundingClientRect().top,
    }));
    expect(positions.sidebarTop).toBeGreaterThanOrEqual(
      positions.topbarBottom - 1,
    );
    expect(positions.sidebarTop).toBeLessThanOrEqual(
      positions.topbarBottom + 1,
    );
  }
});

test("billing comparison does not show invoice preferences", async ({
  page,
}) => {
  await openWorkspace(page);
  await page.locator('.nav[data-page="billing"]').click();
  await expect(page.locator("#audit-view")).not.toContainText(
    "Invoice preferences",
  );
  await expect(page.locator("#history-toggle")).toHaveCount(0);
});

test("filtered bill comparison replaces the no-lines message with results", async ({
  page,
}) => {
  let auditCalls = 0;
  await page.route("**/api/clients/*/audit**", async (route) => {
    auditCalls += 1;
    const report =
      auditCalls === 1
        ? { client: { id: "C-1001", name: "Northstar" }, rows: [], invoice_count: 0, discrepancy_count: 0 }
        : {
            client: { id: "C-1001", name: "Northstar" },
            rows: [
              {
                period_start: "2026-10-01",
                billing_stream: "SERVICE",
                service_name: "Fuel",
                component_name: "Base",
                contracted: true,
                configured: true,
                contract_rate: 10,
                contract_basis: "USD",
                expected_rate: 10,
                pricing_basis: "USD",
                billed_rate: 10,
                billed_amount: 100,
                issue: null,
                explanation: "Rates match.",
              },
            ],
            invoice_count: 1,
            discrepancy_count: 0,
          };
    await route.fulfill({ json: report });
  });
  await openWorkspace(page);
  await page.locator('.nav[data-page="billing"]').click();
  await expect(page.locator("#audit-results")).toContainText(
    "No billing lines found in this period.",
  );
  await page.locator("#filter-audit").click();
  await expect(page.locator("#audit-results .table-wrap")).toBeVisible();
  await expect(page.locator("#audit-results")).toContainText("Fuel");
  await expect(page.locator("#audit-results")).not.toContainText(
    "No billing lines found in this period.",
  );
});

test("overview renders a recoverable message when an API request fails", async ({
  page,
}) => {
  await page.route("**/api/bootstrap", (route) => route.abort());
  await page.goto("/");
  await signIn(page);
  await expect(page.locator("#main")).toContainText(/failed|network|fetch/i);
});
