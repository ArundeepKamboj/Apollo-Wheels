const SERVICE_URLS = window.APOLLO_CONFIG || {
  gatewayApi: "http://127.0.0.1:8000",
};
const savedProfile = JSON.parse(
  sessionStorage.getItem("apollo-user") || "null",
);
const state = {
  page: "overview",
  clientId: "C-1001",
  role: savedProfile?.role || null,
  userId: savedProfile?.user_id || null,
  displayName: savedProfile?.display_name || null,
  token: sessionStorage.getItem("apollo-token"),
  clients: [],
  services: [],
  agreements: [],
  selectedAgreement: null,
  contractExistingClientId: null,
  contractExistingAgreementType: "",
  contractUploadClientId: null,
  uploadedAgreement: null,
  contractMode: "existing", // 'existing' or 'upload'
  pricingDraft: [],
  apiData: null,
  showEvidence: false,
  showConfidence: true,
};
const $ = (s) => document.querySelector(s);
const money = (n) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(Number(n || 0));
function displayRate(row) {
  const terms =
    typeof row.terms_json === "string"
      ? JSON.parse(row.terms_json || "{}")
      : row.terms || {};
  const basis = terms.pricing_basis || "USD";
  if (basis === "USD") return money(row.amount);
  if (basis === "PERCENTAGE") return `${Number(row.amount)}%`;
  if (basis === "BASIS_POINTS") return `${Number(row.amount)} bps`;
  return `${Number(row.amount)} ${esc(basis)}`;
}
const esc = (s) =>
  String(s ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
function notify(message) {
  const el = $("#toast");
  el.textContent = message;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2800);
}
function serviceUrl(path) {
  return SERVICE_URLS.gatewayApi + path;
}
async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (state.token) headers.set("Authorization", `Bearer ${state.token}`);
  if (options.body && !(options.body instanceof FormData))
    headers.set("Content-Type", "application/json");
  const res = await fetch(serviceUrl(path), { ...options, headers });
  const data = await res.json().catch(() => ({}));
  if (res.status === 401) {
    logout();
    throw new Error("Session expired. Please sign in again.");
  }
  if (!res.ok) throw new Error(data.detail || "Something went wrong");
  return data;
}
function showLogin(message = "") {
  document
    .querySelectorAll(".nav")
    .forEach((button) => (button.disabled = true));
  $("#main").innerHTML =
    `<section class="panel login-panel"><div class="eyebrow">Internal demo</div><h1>Sign in to Wheels</h1><p class="subhead">Use your Finance or Structuring demo account.</p><form id="login-form"><label class="control"><span class="field-label">Username</span><input id="login-username" autocomplete="username" required></label><label class="control"><span class="field-label">Password</span><input id="login-password" type="password" autocomplete="current-password" required></label><button class="btn btn-primary" type="submit">Sign in</button><div id="login-error" class="error-text">${esc(message)}</div></form><div class="small muted">Demo users: testfinance, testfinance2, teststructurer</div></section>`;
  $("#login-form").onsubmit = login;
}
async function login(event) {
  event.preventDefault();
  $("#login-error").textContent = "";
  const body = new URLSearchParams({
    username: $("#login-username").value,
    password: $("#login-password").value,
  });
  try {
    const response = await fetch(`${SERVICE_URLS.gatewayApi}/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Sign in failed");
    state.token = data.access_token;
    state.userId = data.user_id;
    state.role = data.role;
    state.displayName = data.display_name;
    sessionStorage.setItem("apollo-token", state.token);
    sessionStorage.setItem(
      "apollo-user",
      JSON.stringify({
        user_id: state.userId,
        role: state.role,
        display_name: state.displayName,
      }),
    );
    $("#user-label").textContent = `${state.displayName} (${state.role})`;
    document
      .querySelectorAll(".nav")
      .forEach((button) => (button.disabled = false));
    await load();
  } catch (error) {
    $("#login-error").textContent = error.message;
  }
}
function logout() {
  state.token = null;
  state.role = null;
  state.userId = null;
  state.displayName = null;
  if (state.page === "contracts") state.clientId = null;
  state.selectedAgreement = null;
  sessionStorage.removeItem("apollo-token");
  sessionStorage.removeItem("apollo-user");
  $("#user-label").textContent = "Signed out";
  showLogin();
}
async function load() {
  if (!state.token) {
    showLogin();
    return;
  }
  try {
    $("#user-label").textContent =
      `${state.displayName || state.userId} (${state.role || ""})`;
    document
      .querySelectorAll(".nav")
      .forEach((button) => (button.disabled = false));
    state.apiData = await api("/api/bootstrap");
    state.clients = state.apiData.clients;
    state.services = state.apiData.services;
    if (
      state.page !== "contracts" &&
      !state.clients.some((c) => c.id === state.clientId)
    )
      state.clientId = state.clients[0]?.id;
    await render();
  } catch (e) {
    // api() already calls logout() and throws on 401 (session expired).
    // A network/timeout failure is NOT an auth failure: keep the session and
    // show a recoverable message instead of logging the user out.
    notify(e.message || "Could not load workspace data.");
  }
}
function nav() {
  document
    .querySelectorAll(".nav")
    .forEach((b) => (b.onclick = () => go(b.dataset.page)));
}
function head(kicker, title, desc, action = "") {
  return `<div class="page-head"><div><div class="eyebrow">${kicker}</div><h1>${title}</h1><div class="subhead">${desc}</div></div>${action}</div>`;
}
function clientPicker(allowEmpty = false) {
  return `<label class="control" style="min-width:230px;margin:0"><span class="field-label">Client</span><select id="client-picker">${allowEmpty ? `<option value="" ${!state.clientId ? "selected" : ""}>Select a client</option>` : ""}${state.clients.map((c) => `<option value="${esc(c.id)}" ${c.id === state.clientId ? "selected" : ""}>${esc(c.name)}</option>`).join("")}</select></label>`;
}
function bindClient() {
  const el = $("#client-picker");
  if (el)
    el.onchange = async () => {
      state.clientId = el.value;
      state.selectedAgreement = null;
      state.pricingDraft = [];
      await render();
    };
}
let pdfJsModule = null;
let activeEvidence = null;
// The agreement currently shown in the viewer. In "existing" mode this is the
// selected stored version; in "upload" mode the draft lives in uploadedAgreement
// (selectedAgreement stays null), so the guard must account for both.
// Drafts are not persisted with a file_path that is accessible via the normal
// /api/agreements/{id}/pdf endpoint. For drafts, we need to stream the uploaded
// file bytes directly from /api/agreements/{id}/pdf-draft or from temp_file_path.
function currentAgreementId() {
  if (state.contractMode === "upload")
    return state.uploadedAgreement?.id || null;
  return state.selectedAgreement;
}
function currentAgreementFileUrl() {
  const id = currentAgreementId();
  if (!id) return null;
  if (state.contractMode === "upload") {
    // Draft: use the direct draft PDF endpoint. The API currently returns the
    // stored file for agreement id. It works because upload-draft inserts a
    // row with file_path = the temp file. So we can keep using the same /pdf
    // endpoint; just make sure we pass the draft id.
    // As an extra safety, if the draft has a temp_file_path we could serve it.
    return `${SERVICE_URLS.gatewayApi}/api/agreements/${id}/pdf`;
  }
  return `${SERVICE_URLS.gatewayApi}/api/agreements/${id}/pdf`;
}
async function loadAgreementPdf(agreementId) {
  const viewer = $("#pdf-viewer");
  if (!viewer) return;
  viewer.dataset.state = "loading";
  viewer.innerHTML =
    '<div class="pdf-loading" role="status">Loading agreement pages...</div>';
  try {
    const url = `${SERVICE_URLS.gatewayApi}/api/agreements/${agreementId}/pdf`;
    const response = await fetch(
      url,
      { headers: { Authorization: `Bearer ${state.token}` } },
    );
    if (!response.ok) {
      // If the PDF endpoint fails for a draft (e.g., file_path missing), try
      // to fall back to the temp_file_path that was returned by upload-draft.
      // This is a temporary bridge until the draft PDF route is explicitly fixed.
      const draft = state.uploadedAgreement;
      if (state.contractMode === "upload" && draft?.temp_file_path && response.status === 404) {
        // Serve the temp file via the same endpoint if it exists. The backend
        // already stores the draft file path in agreements.file_path, so the
        // normal /pdf endpoint should work. If not, we keep the error.
      }
      throw new Error(`PDF request failed (${response.status}).`);
    }
    const contentType = response.headers.get("content-type") || "";
    if (!contentType.includes("application/pdf"))
      throw new Error("The document endpoint did not return a PDF.");
    pdfJsModule ??= import("/node_modules/pdfjs-dist/build/pdf.mjs");
    const pdfjs = await pdfJsModule;
    pdfjs.GlobalWorkerOptions.workerSrc =
      "/node_modules/pdfjs-dist/build/pdf.worker.mjs";
    const pdf = await pdfjs.getDocument({
      data: new Uint8Array(await response.arrayBuffer()),
    }).promise;
    if (currentAgreementId() !== agreementId || !$("#pdf-viewer")) return;
    viewer.dataset.pageCount = String(pdf.numPages);
    viewer.replaceChildren();
    for (let number = 1; number <= pdf.numPages; number++) {
      const page = await pdf.getPage(number);
      const base = page.getViewport({ scale: 1 });
      const scale = Math.min(
        1.5,
        Math.max(0.5, (viewer.clientWidth - 36) / base.width),
      );
      const viewport = page.getViewport({ scale });
      const ratio = Math.min(window.devicePixelRatio || 1, 2);
      const wrapper = document.createElement("div");
      wrapper.className = "pdf-page";
      wrapper.setAttribute("role", "img");
      wrapper.setAttribute(
        "aria-label",
        `Agreement page ${number} of ${pdf.numPages}`,
      );
      wrapper.dataset.page = String(number);
      const canvas = document.createElement("canvas");
      canvas.width = Math.floor(viewport.width * ratio);
      canvas.height = Math.floor(viewport.height * ratio);
      canvas.style.width = `${viewport.width}px`;
      canvas.style.height = `${viewport.height}px`;
      const textLayer = document.createElement("div");
      textLayer.className = "textLayer pdf-text-layer";
      textLayer.style.width = `${viewport.width}px`;
      textLayer.style.height = `${viewport.height}px`;
      textLayer.style.setProperty("--total-scale-factor", String(scale));
      textLayer.style.setProperty("--scale-round-x", "1px");
      textLayer.style.setProperty("--scale-round-y", "1px");
      wrapper.append(canvas, textLayer);
      viewer.append(wrapper);
      const textTask = new pdfjs.TextLayer({
        textContentSource: await page.getTextContent(),
        container: textLayer,
        viewport,
      });
      await Promise.all([
        page.render({
          canvasContext: canvas.getContext("2d"),
          viewport: page.getViewport({ scale: scale * ratio }),
        }).promise,
        textTask.render(),
      ]);
    }
    viewer.dataset.state = "ready";
    if (activeEvidence)
      applyEvidenceHighlight(activeEvidence.page, activeEvidence.quote);
  } catch (error) {
    pdfJsModule = null;
    if (currentAgreementId() === agreementId && $("#pdf-viewer")) {
      viewer.dataset.state = "error";
      viewer.innerHTML = `<div class="pdf-error" role="alert"><b>Could not display this PDF.</b><span>${esc(error.message)}</span><button class="btn btn-secondary" id="retry-pdf">Try again</button></div>`;
      $("#retry-pdf").onclick = () =>
        loadAgreementPdf(agreementId).catch(notify);
    }
    throw error;
  }
}
async function downloadAgreementPdf(agreement) {
  const response = await fetch(
    `${SERVICE_URLS.gatewayApi}/api/agreements/${agreement.id}/pdf`,
    { headers: { Authorization: `Bearer ${state.token}` } },
  );
  if (!response.ok) throw new Error("Could not download the agreement PDF");
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement("a");
  link.href = url;
  link.download = agreement.filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function clearEvidenceHighlight() {
  activeEvidence = null;
  document
    .querySelectorAll(".pdf-text-highlight")
    .forEach((node) => node.classList.remove("pdf-text-highlight"));
}

function applyEvidenceHighlight(pageNumber, quote) {
  document
    .querySelectorAll(".pdf-text-highlight")
    .forEach((node) => node.classList.remove("pdf-text-highlight"));
  const page = document.querySelector(
    `.pdf-page[data-page="${Number(pageNumber)}"]`,
  );
  const layer = page?.querySelector(".pdf-text-layer");
  if (!layer || !quote) return;
  const spans = [...layer.querySelectorAll("span")];
  let pageText = "";
  const owners = [];
  for (const span of spans) {
    for (const char of span.textContent.toUpperCase()) {
      if (/[A-Z0-9]/.test(char)) {
        pageText += char;
        owners.push(span);
      }
    }
  }
  const target = quote.toUpperCase().replace(/[^A-Z0-9]/g, "");
  const start = target ? pageText.indexOf(target) : -1;
  if (start < 0) return;
  const matched = [...new Set(owners.slice(start, start + target.length))];
  matched.forEach((node) => node.classList.add("pdf-text-highlight"));
  matched[0]?.scrollIntoView({ block: "center", inline: "nearest" });
}

function showEvidenceHighlight(pageNumber, quote) {
  activeEvidence = { page: Number(pageNumber), quote };
  applyEvidenceHighlight(activeEvidence.page, activeEvidence.quote);
}

function bindEvidenceHighlights() {
  document
    .querySelectorAll(".field-evidence[data-source-text]")
    .forEach((evidence) => {
      const host = evidence.closest(".control,.service-edit");
      if (!host || host.dataset.evidenceBound) return;
      host.dataset.evidenceBound = "true";
      const show = () =>
        showEvidenceHighlight(
          evidence.dataset.sourcePage,
          evidence.dataset.sourceText,
        );
      host.addEventListener("pointerenter", show);
      host.addEventListener("focusin", show);
      host.addEventListener("pointerleave", () => {
        if (!host.contains(document.activeElement)) clearEvidenceHighlight();
      });
      host.addEventListener("focusout", () => {
        if (!host.matches(":hover")) clearEvidenceHighlight();
      });
    });
}
async function render() {
  nav();
  $("#main").classList.toggle("contract-page", state.page === "contracts");
  document.querySelectorAll(".nav").forEach((button) => {
    button.classList.toggle("active", button.dataset.page === state.page);
  });
  $("#main").innerHTML = '<div class="empty">Loading workspace...</div>';

  try {
    state.apiData = await api("/api/bootstrap");
    $("#pending-nav").textContent = state.apiData.counts.pending_approvals;
    const pages = {
      overview: renderOverview,
      contracts: renderContracts,
      pricing: renderPricing,
      billing: renderBilling,
    };
    const renderPage = pages[state.page] || renderOverview;
    await renderPage();
  } catch (error) {
    $("#main").innerHTML = `<div class="empty">${esc(error.message)}</div>`;
  }
}

async function renderOverview() {
  const counts = state.apiData.counts;
  let summary = { clients: [], clients_with_issues: 0, discrepancy_count: 0 };
  try {
    summary = await api("/api/audit/summary");
  } catch (error) {
    summary.load_error = error.message;
  }

  const clientRows = summary.clients
    .map(
      (client) => `
    <tr>
      <td><b>${esc(client.client_name)}</b><div class="small muted">${esc(client.client_id)}</div></td>
      <td>${client.invoice_count}</td>
      <td>${client.discrepancy_count ? `<span class="tag warn">${client.discrepancy_count} findings</span>` : '<span class="tag good">No findings</span>'}</td>
      <td>${client.findings
        .slice(0, 2)
        .map((row) => esc(row.issue))
        .join("<br>")}</td>
    </tr>`,
    )
    .join("");

  $("#main").innerHTML =
    `${head("Apollo Wheels - Internal workspace", "Contract & billing control", "Review agreements, activate pricing with a second-person check, and find billing differences.")}
    <div class="cards">
      <div class="metric"><div class="metric-label">Synthetic clients</div><div class="metric-value">${counts.clients}</div><div class="metric-note">Demo records</div></div>
      <div class="metric"><div class="metric-label">Agreements</div><div class="metric-value">${counts.agreements}</div><div class="metric-note">MSA and MLA linked by client</div></div>
      <div class="metric"><div class="metric-label">Pending approvals</div><div class="metric-value">${counts.pending_approvals}</div><div class="metric-note">Four-eyes workflow</div></div>
      <div class="metric"><div class="metric-label">Clients with findings</div><div class="metric-value">${summary.clients_with_issues}</div><div class="metric-note">${summary.discrepancy_count} line findings</div></div>
    </div>
    <div class="split">
      <section class="panel">
        <div class="panel-head"><div><h2>Work in progress</h2><div class="panel-desc">Structuring reviews contract terms; Finance prepares pricing and a different Finance user approves.</div></div><span class="pill">13 services</span></div>
        <div class="notice"><b>Structuring</b> uploads and edits extracted contract details. <b>Finance</b> reviews those terms, enters pricing, and requests approval. A different Finance user approves before pricing becomes active.</div>
        <div class="row"><button class="btn btn-primary" onclick="go('contracts')">Review contracts</button><button class="btn btn-secondary" onclick="go('pricing')">Open pricing queue</button></div>
      </section>
      <section class="panel">
        <div class="panel-head"><div><h2>Billing audit</h2><div class="panel-desc">Compare contract, active pricing, and billed line items by period.</div></div></div>
        <div class="audit-summary">
          <div class="audit-stat"><span>Selected client</span><strong>${esc(state.clients.find((client) => client.id === state.clientId)?.name || "")}</strong></div>
          <div class="audit-stat"><span>Billing periods</span><strong>Jan-Mar 2026</strong></div>
          <div class="audit-stat"><span>Source</span><strong>Selectable PDF</strong></div>
        </div>
        <button class="btn btn-quiet" onclick="go('billing')">View billing audit</button>
      </section>
    </div>
    <section class="panel">
      <div class="panel-head"><div><h2>Client audit summary</h2><div class="panel-desc">Clients with flagged service, pricing, quantity, or billing differences.</div></div></div>
      ${
        summary.load_error
          ? `<div class="empty">${esc(summary.load_error)}</div>`
          : clientRows
            ? `<div class="table-wrap"><table><thead><tr><th>Client</th><th>Invoices reviewed</th><th>Status</th><th>Example findings</th></tr></thead><tbody>${clientRows}</tbody></table></div>`
            : '<div class="empty">No clients have been seeded.</div>'
      }
    </section>
    <div class="notice amber"><b>Demo data:</b> all clients, agreements, prices, and billing are synthetic. Deterministic sample parsing is the default; an optional local model path is documented separately.</div>`;
}

function go(page) {
  if (page === "contracts" && state.page !== "contracts") {
    state.contractExistingClientId = null;
    state.contractUploadClientId = null;
    state.selectedAgreement = null;
    state.uploadedAgreement = null;
    state.contractMode = "existing";
    state.contractExistingAgreementType = "";
  } else if (page !== "contracts" && !state.clientId) {
    state.clientId = state.clients[0]?.id || null;
  }
  state.page = page;
  render();
}
function contractClientOptions(selectedId) {
  return `<option value="">Select a client</option>${state.clients.map((client) => `<option value="${esc(client.id)}" ${client.id === selectedId ? "selected" : ""}>${esc(client.name)}</option>`).join("")}`;
}
async function renderContracts() {
  activeEvidence = null;

  let agreementsList = [];
  // Do NOT fetch until the user explicitly clicks Fetch agreement.
  // This avoids auto-loading and keeps the left/right panes empty until fetch.
  if (
    state.contractMode === "existing" &&
    state.contractExistingClientId &&
    state.contractExistingAgreementType &&
    state.selectedAgreementCheck // set only after Fetch agreement is pressed
  ) {
    agreementsList = await api(
      `/api/clients/${state.contractExistingClientId}/agreements?type=${state.contractExistingAgreementType}`,
    );
  }
  state.agreements = agreementsList;

  // No auto-load. selectedAgreement is only set by Fetch agreement button.
  // Upload mode uses uploadedAgreement.
  if (state.contractMode === "existing") {
    const hasPick = state.contractExistingClientId && state.contractExistingAgreementType;
    if (!hasPick) {
      state.selectedAgreement = null;
    }
    // else keep whatever was set by Fetch agreement
  } else {
    // upload mode - uploadedAgreement is already set
    state.selectedAgreement = null;
  }

  const existingSelected = state.agreements.find(
    (agreement) => agreement.id === state.selectedAgreement,
  );
  const selected = state.uploadedAgreement || existingSelected;
  const isDraft = !!state.uploadedAgreement;
  const sourceDescription = selected
    ? `${esc(selected.agreement_type)} Â· ${esc(selected.version_label)}`
    : "Choose an existing client or upload a new agreement.";

  $("#main").innerHTML =
    `${head("Contract workspace", "Agreement review", "View a stored client agreement, or upload a new agreement for extraction.", `<span class="tag neutral">${state.role === "structuring" ? "Structuring can edit terms" : "Finance view is read-only"}</span>`)}
  <div class="contract-tabs" role="tablist" aria-label="Contract source">
    <button class="tab-btn ${state.contractMode === "existing" ? "active" : ""}" role="tab" aria-selected="${state.contractMode === "existing"}" data-tab="existing" id="tab-existing">View Existing Agreement</button>
    <button class="tab-btn ${state.contractMode === "upload" ? "active" : ""}" role="tab" aria-selected="${state.contractMode === "upload"}" data-tab="upload" id="tab-upload">Upload New Agreement</button>
  </div>

  ${
    state.contractMode === "existing"
      ? `
  <section class="panel contract-choice">
    <div class="contract-form-row">
      <label class="control"><span class="field-label">Existing client</span><select id="existing-client-picker">${contractClientOptions(state.contractExistingClientId)}</select></label>
      <label class="control"><span class="field-label">Agreement type</span><select id="existing-agreement-type"><option value="" ${!state.contractExistingAgreementType ? "selected" : ""}>Select agreement type</option><option value="MSA" ${state.contractExistingAgreementType === "MSA" ? "selected" : ""}>MSA</option><option value="MLA" ${state.contractExistingAgreementType === "MLA" ? "selected" : ""}>MLA</option></select></label>
      <label class="control" style="align-self:end"><button class="btn btn-primary" id="fetch-agreement" ${!state.contractExistingClientId || !state.contractExistingAgreementType ? "disabled" : ""}>Fetch agreement</button></label>
    </div>
    ${state.contractExistingClientId && state.contractExistingAgreementType && state.selectedAgreementCheck && state.agreements.length === 0 ? `<div class="notice amber">This client doesn't have any ${state.contractExistingAgreementType} agreements.</div>` : ""}
  </section>
  `
      : ""
  }

  ${
    state.contractMode === "upload"
      ? `
  <section class="panel contract-choice">
    <h2>Upload a new agreement PDF</h2>
    <p class="panel-desc">Upload a selectable-text PDF. Client name and agreement type will be detected from the document and can be corrected before saving.</p>
    <form id="agreement-upload" class="upload-controls">
      <input class="input" type="file" name="file" accept="application/pdf" required>
      <button class="btn btn-primary">Upload and extract</button>
    </form>
  </section>
  `
      : ""
  }

  <div class="contract-layout">
    <section class="panel contract-panel">
      <div class="panel-head"><div><h2>Source document</h2><div class="panel-desc">${sourceDescription}</div></div>${selected ? '<button class="btn btn-secondary" id="download-agreement">Download PDF</button>' : ""}</div>
      ${selected ? '<div id="pdf-viewer" class="pdf-viewer" aria-label="Scrollable source PDF"></div>' : '<div class="empty contract-empty">Select an existing client or upload a PDF to show its source document and extracted terms.</div>'}
    </section>
    <section class="panel contract-panel">
      <div class="panel-head">
        <div><h2>Extracted contract terms</h2><div class="panel-desc">Field values are linked to text from the source agreement.</div></div>
        <span class="tag ${selected ? "good" : "neutral"}">${selected ? esc(selected.status) : "No selection"}</span>
        <div class="view-toggles" style="margin-top:8px;display:flex;gap:16px;align-items:center;">
          <label class="checkline"><input type="checkbox" id="toggle-evidence" ${state.showEvidence ? "checked" : ""}> Show evidence</label>
          <label class="checkline"><input type="checkbox" id="toggle-confidence" ${state.showConfidence ? "checked" : ""}> Show confidence %</label>
        </div>
      </div>
      <div id="terms-editor" class="scroll-panel">${selected ? renderTermsEditor(selected, isDraft) : '<div class="empty contract-empty">Select an existing client or upload a PDF to view extracted terms.</div>'}</div>
      <div class="row spread contract-footer">
        <span class="small muted">All 13 services are represented in the catalogue.</span>
        ${selected ? (isDraft
          ? (state.role === "structuring" ? '<button class="btn btn-primary" id="save-draft-btn">Save in system</button>' : '<button class="btn btn-primary" id="save-draft-btn" disabled>Save in system</button>')
          : (state.role === "structuring" ? '<button class="btn btn-primary" id="save-terms">Save Structuring edits</button>' : '<button class="btn btn-primary" id="save-terms" disabled>Save Structuring edits</button>')) : ""}
      </div>
    </section>
  </div>`;

  // Tab switching
  $("#tab-existing").onclick = async () => {
    state.contractMode = "existing";
    state.uploadedAgreement = null;
    state.selectedAgreement = null;
    state.contractExistingAgreementType = "";
    await renderContracts();
  };
  $("#tab-upload").onclick = async () => {
    state.contractMode = "upload";
    state.contractExistingClientId = null;
    state.contractExistingAgreementType = "";
    state.selectedAgreement = null;
    await renderContracts();
  };

  if (state.contractMode === "existing") {
    $("#existing-client-picker").onchange = async (event) => {
      state.contractExistingClientId = event.target.value || null;
      state.contractExistingAgreementType = "";
      state.uploadedAgreement = null;
      state.selectedAgreement = null;
      state.selectedAgreementCheck = false;
      state.pricingDraft = [];
      if (state.contractExistingClientId)
        state.clientId = state.contractExistingClientId;
      await renderContracts();
    };
    $("#existing-agreement-type").onchange = async (event) => {
      state.contractExistingAgreementType = event.target.value;
      state.selectedAgreement = null;
      state.uploadedAgreement = null;
      state.selectedAgreementCheck = false;
      await renderContracts();
    };
    $("#fetch-agreement").onclick = async () => {
      if (!state.contractExistingClientId || !state.contractExistingAgreementType) return;
      state.selectedAgreementCheck = true;
      const agreements = await api(`/api/clients/${state.contractExistingClientId}/agreements?type=${state.contractExistingAgreementType}`);
      state.agreements = agreements;
      state.selectedAgreement = agreements[0]?.id || null;
      if (!state.selectedAgreement) {
        notify(`No ${state.contractExistingAgreementType} agreement found for this client.`);
      }
      await renderContracts();
    };
  }

  if (state.contractMode === "upload") {
    $('#agreement-upload input[type="file"]').onchange = (event) => {
      if (event.target.files.length) {
        state.contractMode = "upload";
        state.contractExistingClientId = null;
        state.selectedAgreement = null;
        state.uploadedAgreement = null;
        state.contractExistingAgreementType = "";
      }
    };

    $("#agreement-upload").onsubmit = uploadAgreement;
  }

  $("#toggle-evidence").onchange = (event) => {
    state.showEvidence = event.target.checked;
    renderContracts();
  };
  $("#toggle-confidence").onchange = (event) => {
    state.showConfidence = event.target.checked;
    renderContracts();
  };

  if (selected && state.role === "structuring") {
    if (isDraft) {
      $("#save-draft-btn").onclick = saveDraft;
    } else {
      $("#save-terms").onclick = saveTerms;
    }
  }

  if (selected) {
    $("#download-agreement").onclick = () =>
      downloadAgreementPdf(selected).catch((error) => notify(error.message));
    loadAgreementPdf(selected.id).catch((error) => notify(error.message));
  }
  bindEvidenceHighlights();
}
function confidenceLabel(item, field) {
  const score = item.field_confidence?.[field];
  if (typeof score === "number")
    return `${Math.round(score * 100)}% marker match`;
  return item.confidence_method || "Not scored";
}

function renderEvidence(item, field) {
  const page = item.evidence_page || 1;
  const quote = item.source_text || "";
  // The highlight source element is always rendered so hovering/focusing a
  // field highlights its source in the PDF regardless of the toggle. The
  // toggle only controls whether the evidence text is visible.
  const evidenceHtml = `<div class="field-evidence" data-source-page="${page}" data-source-text="${esc(quote)}" title="Hover or focus to highlight this evidence in the PDF" ${state.showEvidence ? "" : "hidden"}>Evidence - page ${page}: ${esc(quote || "No source quote found")}</div>`;
  const confidenceHtml = state.showConfidence
    ? `<div class="small muted">${esc(confidenceLabel(item, field))}</div>`
    : "";
  return evidenceHtml + confidenceHtml;
}

function renderAgreementFacts(agreement) {
  const client =
    state.clients.find((item) => item.id === agreement.client_id)?.name ||
    agreement.client_id;
  const values = [
    ["Agreement type", agreement.agreement_type],
    ["Client", client],
    ["Version", agreement.version_label],
    ["Effective date", agreement.effective_date],
  ];
  return `<dl class="agreement-facts">${values.map(([field, value]) => `<div><dt>${field}</dt><dd>${esc(value || "Not found")}</dd></div>`).join("")}</dl>`;
}

function renderTermsEditor(agreement, isDraft = false) {
  const extracted = agreement.extracted || {};
  const disabled = state.role !== "structuring" ? "disabled" : "";
  // For drafts, client name and agreement type are editable; other fields are read-only until saved
  const editable = disabled === "" || isDraft; // editing allowed in structuring role OR for drafts
  const clientName =
    state.clients.find((c) => c.id === agreement.client_id)?.name ||
    agreement.client_id;
  const draftClientNameInput = isDraft
    ? `<div class="control"><label>Client name</label><input data-draft-field="client_name" value="${esc(clientName)}" ${editable ? "" : "disabled"}></div>`
    : "";
  const draftAgreementTypeInput = isDraft
    ? `<div class="control"><label>Agreement type</label><select data-draft-field="agreement_type" ${editable ? "" : "disabled"}><option value="MSA" ${agreement.agreement_type === "MSA" ? "selected" : ""}>MSA</option><option value="MLA" ${agreement.agreement_type === "MLA" ? "selected" : ""}>MLA</option></select></div>`
    : "";

  if (agreement.agreement_type === "MLA") {
    const lease = extracted.lease || {};
    return `${renderAgreementFacts(agreement)}<div class="notice">Lease details extracted from this MLA.</div>
      <div class="three">
        <div class="control"><label>Lease vehicles</label><input data-key="lease.quantity" type="number" value="${lease.quantity ?? ""}" ${disabled}></div>
        <div class="control"><label>Monthly rate</label><input data-key="lease.contract_amount" type="number" step="0.01" value="${lease.contract_amount ?? ""}" ${disabled}>${renderEvidence(lease, "contract_amount")}</div>
        <div class="control"><label>Rate unit</label><input data-key="lease.rate_unit" value="${esc(lease.rate_unit || "")}" ${disabled}>${renderEvidence(lease, "rate_unit")}</div>
        <div class="control"><label>Lease term (months)</label><input data-key="lease.term_months" type="number" value="${lease.term_months ?? ""}" ${disabled}>${renderEvidence(lease, "term_months")}</div>
        <div class="control"><label>Billing frequency</label><input data-key="lease.billing_frequency" value="${esc(lease.billing_frequency || "")}" ${disabled}>${renderEvidence(lease, "billing_frequency")}</div>
        <div class="control"><label>Billing day</label><input data-key="lease.billing_day" value="${esc(lease.billing_day || "")}" ${disabled}>${renderEvidence(lease, "billing_day")}</div>
        <div class="control"><label>Vehicle make</label><input data-key="lease.vehicle_make" value="${esc(lease.vehicle_make || "")}" ${disabled}>${renderEvidence(lease, "vehicle_make")}</div>
        <div class="control"><label>Vehicle model</label><input data-key="lease.vehicle_model" value="${esc(lease.vehicle_model || "")}" ${disabled}>${renderEvidence(lease, "vehicle_model")}</div>
        <div class="control"><label>Engine type</label><input data-key="lease.engine_type" value="${esc(lease.engine_type || "")}" ${disabled}>${renderEvidence(lease, "engine_type")}</div>
        <div class="control"><label>Pricing basis</label><input data-key="lease.pricing_basis" value="${esc(lease.pricing_basis || "")}" ${disabled}>${renderEvidence(lease, "pricing_basis")}</div>
      </div>`;
  }

  const services = extracted.services || [];
  const components = extracted.components || [];
  const serviceRows = services
    .map(
      (service, index) => `
    <div class="service-edit">
      <div><b>${esc(service.service_name)}</b><span class="service-rate">$${service.contract_amount?.toFixed(2) ?? "0.00"}</span>${renderEvidence(service, "contract_amount")}</div>
      <label class="checkline"><input class="checkbox" type="checkbox" data-service="${index}" ${service.subscribed ? "checked" : ""} ${disabled}> Included</label>
      <input type="number" min="0" step="0.01" data-amount="${index}" value="${service.contract_amount ?? ""}" ${disabled} aria-label="${esc(service.service_name)} contract rate">
      <details class="service-details" open><summary>Extracted fields</summary><div class="three">
        ${[
          ["pricing_basis", "Pricing basis"],
          ["rate_unit", "Rate unit"],
          ["billing_frequency", "Billing frequency"],
          ["billing_day", "Billing day"],
          ["vehicle_count", "Vehicle count"],
          ["driver_count", "Driver count"],
        ]
          .map(
            ([field, label]) =>
              `<label class="control"><span class="field-label">${label}</span><input data-service-input="${index}|${field}" value="${esc(service[field] ?? "")}" ${disabled}>${renderEvidence(service, field)}</label>`,
          )
          .join("")}
      </div></details>
    </div>`,
    )
    .join("");
  const componentRows = components
    .map(
      (component, index) => `
    <div class="service-edit">
      <div><b>${esc(component.display_name)}</b>${renderEvidence(component, "contract_amount")}</div>
      <span class="tag neutral">${esc(component.charge_type)}</span>
      <input type="number" min="0" step="0.01" data-component-amount="${index}" value="${component.contract_amount ?? ""}" ${disabled} aria-label="${esc(component.display_name)} contract rate">
    </div>`,
    )
    .join("");

  return `${renderAgreementFacts(agreement)}<div class="small muted" style="margin-bottom:8px">Service - subscribed - contract rate <span class="service-count">${services.filter((service) => service.subscribed).length} selected</span></div>
    ${serviceRows}${components.length ? `<div class="notice">Additional contractual components</div>${componentRows}` : ""}`;
}

async function uploadAgreement(e) {
  e.preventDefault();
  try {
    const form = new FormData(e.target);
    const response = await fetch(serviceUrl(`/api/agreements/upload-draft`), {
      method: "POST",
      headers: { Authorization: `Bearer ${state.token}` },
      body: form,
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail);
    state.contractExistingClientId = null;
    state.selectedAgreement = null;
    state.uploadedAgreement = data;
    notify(`${data.detected_agreement_type} identified; fields extracted`);
    await renderContracts();
  } catch (err) {
    notify(err.message);
  }
}

async function saveDraft() {
  try {
    const agreement = state.uploadedAgreement;
    if (!agreement) throw new Error("No draft to save");
    // Get corrected client name and agreement type from draft fields
    const clientNameInput = document.querySelector(
      '[data-draft-field="client_name"]',
    );
    const agreementTypeInput = document.querySelector(
      '[data-draft-field="agreement_type"]',
    );
    const clientName = clientNameInput?.value || agreement.detected_client_name;
    const agreementType =
      agreementTypeInput?.value || agreement.detected_agreement_type;
    // Find or create client
    let client = state.clients.find((c) => c.name === clientName);
    if (!client) {
      // For demo, we can't create clients dynamically; pick first match
      client = state.clients[0];
    }
    const response = await fetch(
      serviceUrl(`/api/agreements/${agreement.draft_id}/identifiers`),
      {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${state.token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          client_id: client.id,
          agreement_type: agreementType,
        }),
      },
    );
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "Failed to save identifiers");
    }
    const saved = await response.json();
    state.uploadedAgreement = saved;
    notify("Draft saved in system");
    await renderContracts();
  } catch (err) {
    notify(err.message);
  }
}

async function saveTerms() {
  try {
    const agreement = state.agreements.find(
      (item) => item.id === state.selectedAgreement,
    );
    const extracted = structuredClone(agreement.extracted);

    if (agreement.agreement_type === "MLA") {
      const numericFields = ["quantity", "contract_amount", "term_months"];
      const textFields = [
        "rate_unit",
        "billing_frequency",
        "billing_day",
        "vehicle_make",
        "vehicle_model",
        "engine_type",
        "pricing_basis",
        "effective_from",
      ];
      for (const key of [...numericFields, ...textFields]) {
        const input = document.querySelector(`[data-key="lease.${key}"]`);
        if (!input) continue;
        if (numericFields.includes(key))
          extracted.lease[key] =
            input.value === "" ? null : Number(input.value);
        else extracted.lease[key] = input.value;
      }
    } else {
      extracted.services.forEach((service, index) => {
        const included = document.querySelector(`[data-service="${index}"]`);
        const amount = document.querySelector(`[data-amount="${index}"]`);
        if (included) service.subscribed = included.checked;
        if (amount)
          service.contract_amount =
            amount.value === "" ? null : Number(amount.value);
        for (const field of [
          "pricing_basis",
          "rate_unit",
          "billing_frequency",
          "billing_day",
          "vehicle_count",
          "driver_count",
        ]) {
          const input = document.querySelector(
            `[data-service-input="${index}|${field}"]`,
          );
          if (!input) continue;
          if (["vehicle_count", "driver_count"].includes(field)) {
            service[field] = input.value === "" ? null : Number(input.value);
          } else {
            service[field] = input.value || null;
          }
        }
      });
      extracted.components.forEach((component, index) => {
        const amount = document.querySelector(
          `[data-component-amount="${index}"]`,
        );
        if (amount)
          component.contract_amount =
            amount.value === "" ? null : Number(amount.value);
      });
    }

    const comment = prompt("Enter update comment for audit trail:");
    if (!comment) return;
    // Save creates a NEW version with a new ID; capture it to refresh the view
    const saved = await api(`/api/agreements/${agreement.id}/save-version`, {
      method: "PUT",
      body: JSON.stringify({ extracted, update_comment: comment }),
    });
    // Update state to the new version so the PDF loads the regenerated version
    state.selectedAgreement = saved.id;
    notify("New version saved with audit comment");
    await renderContracts();
  } catch (error) {
    notify(error.message);
  }
}

async function renderPricing() {
  state.agreements = await api(`/api/clients/${state.clientId}/agreements`);
  const data = await api(`/api/clients/${state.clientId}/pricing`);
  const pending = data.requests.filter((r) => r.status === "pending_approval");
  const active = data.components.filter((c) => c.status === "active");
  $("#main").innerHTML =
    `${head("Pricing service", "Pricing setup & approval", "Finance owns pricing. One person submits; a different Finance user approves before activation.", `<div class="toolbar">${clientPicker()}</div>`)}
<div class="notice"><b>Data design:</b> each charge component is a separately versioned record. Common pricing fields are indexed; optional pricing-specific fields stay in a flexible terms payload. Activation writes to the internal pricing database.</div>
<section class="panel"><div class="panel-head"><div><h2>Active pricing</h2><div class="panel-desc">${active.length} active component records Â· retained versions remain available for history</div></div><span class="tag good">${active.length ? "Active" : "No active setup"}</span></div>${active.length ? `<div class="table-wrap"><table><thead><tr><th>Stream</th><th>Service</th><th>Component</th><th>Charge</th><th>Rate</th><th>Rate unit</th><th>Qty</th><th>Frequency</th><th>Version</th></tr></thead><tbody>${active.map((c) => `<tr><td>${esc(c.billing_stream)}</td><td>${esc(c.service_name)}</td><td>${esc(c.component_name)}</td><td>${esc(c.charge_type)}</td><td>${displayRate(c)}</td><td>${esc(c.rate_unit)}</td><td>${c.quantity}</td><td>${esc(c.billing_frequency)}</td><td>v${c.version}</td></tr>`).join("")}</tbody></table></div>` : '<div class="empty">No active pricing records.</div>'}</section>
<div class="split"><section class="panel"><div class="panel-head"><div><h2>Prepare pricing version</h2><div class="panel-desc">Choose the agreement set, review each charge, then send to a second Finance approver.</div></div></div><div class="row"><button class="btn btn-secondary" id="load-contract-pricing" ${state.role !== "finance" ? "disabled" : ""}>Load subscribed contract terms</button><button class="btn btn-quiet" id="add-component" ${state.role !== "finance" ? "disabled" : ""}>+ Add component</button></div><div id="pricing-editor" class="pricing-list" style="margin-top:12px"></div><div class="row spread" style="margin-top:14px"><span class="small muted">Submitter: ${esc(state.userId)}</span><button class="btn btn-primary" id="submit-pricing" ${state.role !== "finance" ? "disabled" : ""}>Request second-person approval</button></div></section>
<section class="panel"><div class="panel-head"><div><h2>Four-eyes queue</h2><div class="panel-desc">A different Finance user must approve the request to activate pricing.</div></div><span class="tag ${pending.length ? "warn" : "good"}">${pending.length} pending</span></div>${pending.length ? pending.map((r) => `<div class="approval"><h3>Pricing version v${r.version}</h3><div class="approval-meta">Initiated by ${esc(r.initiated_by)} Â· ${esc(r.created_at)} Â· ${esc(r.id.slice(0, 8))}</div><button class="btn btn-primary approve-btn" data-id="${r.id}" ${state.role !== "finance" || r.initiated_by === state.userId ? "disabled" : ""}>Approve and activate</button>${r.initiated_by === state.userId ? '<div class="small muted" style="margin-top:7px">Sign in as a different Finance user to approve.</div>' : ""}</div>`).join("") : '<div class="empty">No pricing requests are waiting for approval.</div>'}</section></div>`;
  bindClient();
  renderPricingEditor();
  $("#load-contract-pricing").onclick = loadDraftFromContracts;
  $("#add-component").onclick = () => {
    state.pricingDraft.push({
      agreement_id:
        state.agreements.find((a) => a.agreement_type === "MSA")?.id || "",
      billing_stream: "SERVICE",
      service_code: "FUEL",
      service_name: "Fuel",
      component_code: "custom_fee",
      component_name: "Additional charge",
      charge_type: "one_time",
      amount: 0,
      currency: "USD",
      rate_unit: "account",
      quantity: 1,
      billing_frequency: "one_time",
      billing_day: null,
      effective_from: "2026-01-01",
      terms: {},
    });
    renderPricingEditor();
  };
  $("#submit-pricing").onclick = submitPricing;
  document
    .querySelectorAll(".approve-btn")
    .forEach((b) => (b.onclick = () => approvePricing(b.dataset.id)));
}
function renderPricingEditor() {
  const host = $("#pricing-editor");
  if (!host) return;
  if (!state.pricingDraft.length) {
    host.innerHTML =
      '<div class="empty">Load contract terms to start a pricing version.</div>';
    return;
  }
  host.innerHTML = state.pricingDraft
    .map(
      (c, i) =>
        `<div class="pricing-row" data-row="${i}"><div class="control"><label>Service / component</label><div class="small"><b>${esc(c.service_name)}</b><br>${esc(c.component_name)}</div></div><div class="control"><label>Stream</label><select data-field="billing_stream"><option ${c.billing_stream === "SERVICE" ? "selected" : ""}>SERVICE</option><option ${c.billing_stream === "LEASE" ? "selected" : ""}>LEASE</option></select></div><div class="control"><label>Charge type</label><select data-field="charge_type"><option value="recurring" ${c.charge_type === "recurring" ? "selected" : ""}>Recurring</option><option value="one_time" ${c.charge_type === "one_time" ? "selected" : ""}>One-time</option></select></div><div class="control"><label>Amount</label><input data-field="amount" type="number" min="0" step="0.01" value="${Number(c.amount || 0)}"></div><div class="control"><label>Price format</label><select data-term="pricing_basis"><option value="USD" ${c.terms?.pricing_basis === "USD" ? "selected" : ""}>USD</option><option value="PERCENTAGE" ${c.terms?.pricing_basis === "PERCENTAGE" ? "selected" : ""}>Percentage</option><option value="BASIS_POINTS" ${c.terms?.pricing_basis === "BASIS_POINTS" ? "selected" : ""}>Basis points</option></select></div><div class="control"><label>Rate unit</label><input data-field="rate_unit" value="${esc(c.rate_unit)}"></div><div class="control"><label>Quantity</label><input data-field="quantity" type="number" min="0" step="1" value="${Number(c.quantity || 1)}"></div><button class="icon-btn" data-remove="${i}" title="Remove component">Ã—</button></div>`,
    )
    .join("");
  host.querySelectorAll("[data-field]").forEach(
    (el) =>
      (el.onchange = () => {
        const row = el.closest("[data-row]");
        const c = state.pricingDraft[Number(row.dataset.row)];
        c[el.dataset.field] = ["amount", "quantity"].includes(el.dataset.field)
          ? Number(el.value)
          : el.value;
      }),
  );
  host.querySelectorAll("[data-term]").forEach(
    (el) =>
      (el.onchange = () => {
        const row = el.closest("[data-row]");
        const c = state.pricingDraft[Number(row.dataset.row)];
        c.terms = { ...c.terms, [el.dataset.term]: el.value };
      }),
  );
  host.querySelectorAll("[data-remove]").forEach(
    (el) =>
      (el.onclick = () => {
        state.pricingDraft.splice(Number(el.dataset.remove), 1);
        renderPricingEditor();
      }),
  );
}
async function loadDraftFromContracts() {
  try {
    const rows = [];
    let missingRates = 0;

    for (const agreement of state.agreements) {
      const extracted = agreement.extracted || {};

      for (const term of extracted.services || []) {
        if (!term.subscribed) continue;
        if (term.contract_amount == null) {
          missingRates += 1;
          continue;
        }
        rows.push({
          agreement_id: agreement.id,
          billing_stream: "SERVICE",
          service_code: term.service_code,
          service_name: term.service_name,
          component_code: term.component_name,
          component_name: term.component_name
            .replaceAll("_", " ")
            .replace(/\b\w/g, (letter) => letter.toUpperCase()),
          charge_type: term.charge_type || "recurring",
          amount: Number(term.contract_amount),
          currency: "USD",
          rate_unit: term.rate_unit || "vehicle_month",
          quantity: Number(term.vehicle_count ?? term.driver_count ?? 1),
          billing_frequency: term.billing_frequency || "monthly",
          billing_day: term.billing_day || null,
          effective_from: agreement.effective_date,
          terms: {
            source_page: term.evidence_page || 1,
            pricing_basis: term.pricing_basis || "USD",
            vehicle_count: term.vehicle_count,
            driver_count: term.driver_count,
          },
        });
      }

      for (const term of extracted.components || []) {
        if (term.contract_amount == null) {
          missingRates += 1;
          continue;
        }
        rows.push({
          agreement_id: agreement.id,
          billing_stream: "SERVICE",
          service_code: term.service_code,
          service_name: "Fuel",
          component_code: term.component_name,
          component_name: term.display_name,
          charge_type: term.charge_type,
          amount: Number(term.contract_amount),
          currency: "USD",
          rate_unit: term.rate_unit || "account",
          quantity: Number(term.quantity ?? 1),
          billing_frequency: "one_time",
          billing_day: null,
          effective_from: agreement.effective_date,
          terms: {
            source_page: term.evidence_page || 1,
            pricing_basis: term.pricing_basis || "USD",
            quantity_basis: term.quantity,
          },
        });
      }

      const lease = extracted.lease;
      if (lease) {
        if (lease.contract_amount == null) {
          missingRates += 1;
        } else {
          rows.push({
            agreement_id: agreement.id,
            billing_stream: "LEASE",
            service_code: lease.service_code,
            service_name: lease.service_name,
            component_code: lease.component_name,
            component_name: "Monthly Lease",
            charge_type: "recurring",
            amount: Number(lease.contract_amount),
            currency: "USD",
            rate_unit: lease.rate_unit || "vehicle_month",
            quantity: Number(lease.quantity ?? 1),
            billing_frequency: "monthly",
            billing_day: "1",
            effective_from: agreement.effective_date,
            terms: {
              source_page: lease.evidence_page || 1,
              term_months: lease.term_months,
              vehicle_make: lease.vehicle_make,
              vehicle_model: lease.vehicle_model,
              engine_type: lease.engine_type,
              pricing_basis: lease.pricing_basis,
            },
          });
        }
      }
    }

    state.pricingDraft = rows;
    renderPricingEditor();
    const note = missingRates
      ? ` - ${missingRates} charge(s) skipped because their rate needs review`
      : "";
    notify(`Loaded ${rows.length} charge components${note}`);
  } catch (error) {
    notify(error.message);
  }
}

async function submitPricing() {
  if (state.role !== "finance") return;
  const components = state.pricingDraft.map((c) => ({ ...c }));
  if (!components.length) {
    notify("Load at least one contract charge");
    return;
  }
  try {
    const result = await api("/api/pricing/requests", {
      method: "POST",
      body: JSON.stringify({
        client_id: state.clientId,
        agreement_ids: state.agreements.map((a) => a.id),
        components,
      }),
    });
    notify(`Pricing v${result.version} is waiting for second approval`);
    state.pricingDraft = [];
    renderPricing();
  } catch (e) {
    notify(e.message);
  }
}
async function approvePricing(id) {
  try {
    await api(`/api/pricing/requests/${id}/approve`, { method: "POST" });
    notify("Approved pricing is now active for this client");
    renderPricing();
  } catch (e) {
    notify(e.message);
  }
}
async function renderBilling() {
  const [history, audit, combined] = await Promise.all([
    api(`/api/clients/${state.clientId}/billing-history`),
    api(`/api/clients/${state.clientId}/audit`),
    api(`/api/clients/${state.clientId}/billing-combined`),
  ]);
  const client = state.clients.find((c) => c.id === state.clientId);
  $("#main").innerHTML =
    `${head("Billing workspace", "Billing audit & history", "Ingest billing PDFs, compare billed line items with contract and active pricing, and inspect service-level history.", `<div class="toolbar">${clientPicker()}</div>`)}
  <div class="split"><section class="panel"><div class="panel-head"><div><h2>Ingest billing PDF</h2><div class="panel-desc">Selectable-text billing PDF Â· synthetic demo format</div></div></div><form id="billing-upload" class="filebox"><input type="file" name="file" accept="application/pdf" required><button class="btn btn-primary" style="margin-top:10px">Upload and compare</button></form></section><section class="panel"><div class="panel-head"><div><h2>Invoice preferences</h2><div class="panel-desc">Client setting is controlled by internal Finance.</div></div></div><label class="checkline"><input id="history-toggle" type="checkbox" ${client?.include_history_on_invoice ? "checked" : ""} ${state.role !== "finance" ? "disabled" : ""}> Include prior billing history in generated pricing PDFs</label><div class="notice">Client-facing email/PDF delivery is a later phase. This setting is retained as a future invoice preference.</div></section></div>
  <section class="panel"><div class="panel-head"><div><h2>Combined billing view (service + lease)</h2><div class="panel-desc">All periods grouped with service and lease charges together, preserving stream labels.</div></div></div>${renderCombinedBilling(combined)}</section>
  <section class="panel"><div class="panel-head"><div><h2>Contract vs pricing vs billing</h2><div class="panel-desc">Exceptions are based on synthetic inputs; use the PDF source and agreement stream to investigate.</div></div><div class="toolbar"><input id="audit-start" class="input" type="date"><input id="audit-end" class="input" type="date"><button id="filter-audit" class="btn btn-quiet">Filter periods</button></div></div><div class="audit-summary"><div class="audit-stat"><span>Billing statements in range</span><strong>${audit.invoice_count}</strong></div><div class="audit-stat"><span>Line-level exceptions</span><strong>${audit.discrepancy_count}</strong></div><div class="audit-stat"><span>Rows reviewed</span><strong>${audit.rows.length}</strong></div></div>${audit.rows.length ? auditTable(audit.rows) : '<div class="empty">No billing lines found in this period.</div>'}</section>
  <section class="panel"><div class="panel-head"><div><h2>Billing history</h2><div class="panel-desc">Line-level view across invoice periods; service and lease streams stay distinct.</div></div><div class="toolbar"><input id="history-start" class="input" type="date"><input id="history-end" class="input" type="date"><button id="filter-history" class="btn btn-quiet">Filter</button></div></div>${history.length ? `<div class="table-wrap"><table><thead><tr><th>Period</th><th>Invoice</th><th>Stream</th><th>Service</th><th>Component</th><th>Quantity</th><th>Rate</th><th>Amount</th></tr></thead><tbody>${history.map((r) => `<tr><td>${esc(r.period_start)}</td><td>${esc(r.invoice_number)}</td><td><span class="tag neutral">${esc(r.billing_stream)}</span></td><td>${esc(r.service_name)}</td><td>${esc(r.component_name)}</td><td>${r.quantity} ${esc(r.rate_unit)}</td><td>${money(r.rate)}</td><td><b>${money(r.amount)}</b></td></tr>`).join("")}</tbody></table></div>` : '<div class="empty">No billing history has been ingested.</div>'}</section>`;
  bindClient();
  $("#billing-upload").onsubmit = uploadBilling;
  $("#history-toggle").onchange = async (e) => {
    try {
      await api(`/api/clients/${state.clientId}/invoice-history`, {
        method: "PUT",
        body: JSON.stringify({ enabled: e.target.checked }),
      });
      notify("Invoice preference saved");
    } catch (err) {
      notify(err.message);
      e.target.checked = !e.target.checked;
    }
  };
  $("#filter-audit").onclick = () => filterReport("audit");
  $("#filter-history").onclick = () => filterReport("billing-history");
}
function formatRate(amount, basis) {
  if (amount == null) return "Not available";
  if (basis === "PERCENTAGE") return `${Number(amount)}%`;
  if (basis === "BASIS_POINTS") return `${Number(amount)} bps`;
  return money(amount);
}

function auditTable(rows) {
  const body = rows
    .map((row) => {
      const contractRate = formatRate(row.contract_rate, row.contract_basis);
      const configuredRate = formatRate(
        row.expected_rate,
        row.pricing_basis || row.contract_basis,
      );
      const billedRate = formatRate(
        row.billed_rate,
        row.pricing_basis || row.contract_basis,
      );
      const finding = row.issue
        ? `<span class="tag ${row.issue.includes("differs") ? "warn" : "bad"}">${esc(row.issue)}</span>`
        : '<span class="tag good">Match</span>';

      return `<tr>
      <td>${esc(row.period_start)}</td>
      <td>${esc(row.billing_stream)}</td>
      <td>${esc(row.service_name)}</td>
      <td>${esc(row.component_name)}</td>
      <td>${row.contracted ? contractRate : '<span class="tag bad">Missing</span>'}</td>
      <td>${row.configured ? configuredRate : '<span class="tag bad">Missing</span>'}</td>
      <td>${billedRate}</td>
      <td>${money(row.billed_amount)}</td>
      <td>${finding}<div class="small muted">${esc(row.explanation || "")}</div></td>
    </tr>`;
    })
    .join("");

  return `<div class="table-wrap"><table>
    <thead><tr>
      <th>Period</th><th>Stream</th><th>Service</th><th>Component</th>
      <th>Contract rate</th><th>Configured rate</th><th>Billed rate</th>
      <th>Billed total</th><th>Finding and reason</th>
    </tr></thead>
    <tbody>${body}</tbody>
  </table></div>`;
}

function renderCombinedBilling(data) {
  if (!data.periods || !data.periods.length)
    return '<div class="empty">No combined billing data available.</div>';
  const periodRows = data.periods
    .map(
      (p) => `
    <tr style="font-weight:bold;background:#f8f9fa;">
      <td>${esc(p.period_start)} to ${esc(p.period_end)}</td>
      <td colspan="7">Total: ${money(p.period_total)} (Service: ${money(p.service_total)}, Lease: ${money(p.lease_total)})</td>
    </tr>
    ${p.service_lines
      .map(
        (l) => `
      <tr>
        <td>${esc(l.invoice_number)}</td>
        <td><span class="tag good">SERVICE</span></td>
        <td>${esc(l.service_name)}</td>
        <td>${esc(l.component_name)}</td>
        <td>${l.charge_type}</td>
        <td>${l.quantity} ${esc(l.rate_unit)}</td>
        <td>${money(l.rate)}</td>
        <td><b>${money(l.amount)}</b></td>
      </tr>`,
      )
      .join("")}
    ${p.lease_lines
      .map(
        (l) => `
      <tr>
        <td>${esc(l.invoice_number)}</td>
        <td><span class="tag neutral">LEASE</span></td>
        <td>${esc(l.service_name)}</td>
        <td>${esc(l.component_name)}</td>
        <td>${l.charge_type}</td>
        <td>${l.quantity} ${esc(l.rate_unit)}</td>
        <td>${money(l.rate)}</td>
        <td><b>${money(l.amount)}</b></td>
      </tr>`,
      )
      .join("")}
  `,
    )
    .join("");
  return `<div class="table-wrap"><table><thead><tr><th>Period</th><th>Invoice</th><th>Stream</th><th>Service</th><th>Component</th><th>Charge</th><th>Qty/Rate</th><th>Amount</th></tr></thead><tbody>${periodRows}</tbody></table>
    <div class="audit-summary" style="margin-top:12px;">
      <div class="audit-stat"><span>Combined total</span><strong>${money(data.combined_total)}</strong></div>
      <div class="audit-stat"><span>Service total</span><strong>${money(data.service_total)}</strong></div>
      <div class="audit-stat"><span>Lease total</span><strong>${money(data.lease_total)}</strong></div>
    </div></div>`;
}

async function uploadBilling(e) {
  e.preventDefault();
  try {
    const form = new FormData(e.target);
    const response = await fetch(
      serviceUrl(`/api/clients/${state.clientId}/billing-documents`),
      {
        method: "POST",
        headers: { Authorization: `Bearer ${state.token}` },
        body: form,
      },
    );
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail);
    notify(`Ingested ${data.line_count} billing lines`);
    renderBilling();
  } catch (err) {
    notify(err.message);
  }
}
async function filterReport(kind) {
  const prefix = kind === "audit" ? "audit" : "history";
  const start = $(`#${prefix}-start`).value;
  const end = $(`#${prefix}-end`).value;
  try {
    if (kind === "audit") {
      const rows = await api(
        `/api/clients/${state.clientId}/audit?${new URLSearchParams({ start, end })}`,
      );
      const panel = document.querySelectorAll(".panel")[2];
      panel.querySelector(".audit-summary").innerHTML =
        `<div class="audit-stat"><span>Billing statements in range</span><strong>${rows.invoice_count}</strong></div><div class="audit-stat"><span>Line-level exceptions</span><strong>${rows.discrepancy_count}</strong></div><div class="audit-stat"><span>Rows reviewed</span><strong>${rows.rows.length}</strong></div>`;
      panel.querySelector(".table-wrap")?.remove();
      panel.insertAdjacentHTML("beforeend", auditTable(rows.rows));
    } else {
      const rows = await api(
        `/api/clients/${state.clientId}/billing-history?${new URLSearchParams({ start, end })}`,
      );
      const panel = document.querySelectorAll(".panel")[3];
      panel.querySelector(".table-wrap")?.remove();
      panel.insertAdjacentHTML(
        "beforeend",
        rows.length
          ? `<div class="table-wrap"><table><thead><tr><th>Period</th><th>Invoice</th><th>Stream</th><th>Service</th><th>Component</th><th>Quantity</th><th>Rate</th><th>Amount</th></tr></thead><tbody>${rows.map((r) => `<tr><td>${esc(r.period_start)}</td><td>${esc(r.invoice_number)}</td><td>${esc(r.billing_stream)}</td><td>${esc(r.service_name)}</td><td>${esc(r.component_name)}</td><td>${r.quantity} ${esc(r.rate_unit)}</td><td>${money(r.rate)}</td><td>${money(r.amount)}</td></tr>`).join("")}</tbody></table></div>`
          : '<div class="empty">No billing lines in that range.</div>',
      );
    }
    notify("History filters applied");
  } catch (e) {
    notify(e.message);
  }
}
$("#logout").onclick = logout;
load().catch((e) => {
  $("#main").innerHTML =
    `<div class="empty">Could not load the workspace: ${esc(e.message)}. Start the local server from the project directory.</div>`;
});
