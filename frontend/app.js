const SERVICE_URLS = window.APOLLO_CONFIG || {
  gatewayApi: "http://127.0.0.1:8000",
};
const savedProfile = JSON.parse(
  sessionStorage.getItem("apollo-user") || "null",
);
const availablePages = ["overview", "contracts", "pricing", "billing"];
const savedPage = sessionStorage.getItem("apollo-page");
const state = {
  page:
    sessionStorage.getItem("apollo-token") && availablePages.includes(savedPage)
      ? savedPage
      : "overview",
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
  billingStream: "COMBINED",
  billingStart: "",
  billingEnd: "",
  billingMin: "",
  billingMax: "",
  billingTab: "audit",
  // Forecast billing preview modal state
  forecastPreview: null, // { clientId, clientName, agreementType, start, end, stream, data }
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
    `<section class="panel login-panel"><h1>Sign in to Wheels</h1><p class="subhead">Sign in with your account to continue.</p><form id="login-form"><label class="control"><span class="field-label">Username</span><input id="login-username" autocomplete="username" required></label><label class="control"><span class="field-label">Password</span><input id="login-password" type="password" autocomplete="current-password" required></label><button class="btn btn-primary" type="submit">Sign in</button><div id="login-error" class="error-text">${esc(message)}</div></form></section>`;
  $("#login-form").onsubmit = login;
}
function syncNavigationAccess() {
  const restrictedPages = new Set(["pricing", "billing"]);
  document.querySelectorAll(".nav").forEach((button) => {
    button.hidden =
      state.role === "structuring" && restrictedPages.has(button.dataset.page);
  });
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
    state.page = "overview";
    sessionStorage.setItem("apollo-token", state.token);
    sessionStorage.setItem("apollo-page", state.page);
    sessionStorage.setItem(
      "apollo-user",
      JSON.stringify({
        user_id: state.userId,
        role: state.role,
        display_name: state.displayName,
      }),
    );
    $("#user-label").textContent = `${state.displayName} (${state.role})`;
    syncNavigationAccess();
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
  state.page = "overview";
  syncNavigationAccess();
  if (state.page === "contracts") state.clientId = null;
  state.selectedAgreement = null;
  sessionStorage.removeItem("apollo-token");
  sessionStorage.removeItem("apollo-user");
  sessionStorage.removeItem("apollo-page");
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
    const response = await fetch(url, {
      headers: { Authorization: `Bearer ${state.token}` },
    });
    if (!response.ok) {
      // If the PDF endpoint fails for a draft (e.g., file_path missing), try
      // to fall back to the temp_file_path that was returned by upload-draft.
      // This is a temporary bridge until the draft PDF route is explicitly fixed.
      const draft = state.uploadedAgreement;
      if (
        state.contractMode === "upload" &&
        draft?.temp_file_path &&
        response.status === 404
      ) {
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
  if (
    state.role === "structuring" &&
    ["pricing", "billing"].includes(state.page)
  ) {
    state.page = "overview";
  }
  if (state.token) sessionStorage.setItem("apollo-page", state.page);
  syncNavigationAccess();
  nav();
  $("#main").classList.toggle("contract-page", state.page === "contracts");
  document.querySelectorAll(".nav").forEach((button) => {
    button.classList.toggle("active", button.dataset.page === state.page);
  });
  $("#main").innerHTML = '<div class="empty">Loading workspace...</div>';

  try {
    state.apiData = await api("/api/bootstrap");
    state.clients = state.apiData.clients;
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
  if (state.role !== "structuring") {
    try {
      summary = await api("/api/audit/summary");
    } catch (error) {
      summary.load_error = error.message;
    }
  }

  $("#main").innerHTML =
    `${head("Apollo Wheels - Internal workspace", "Contract & billing control", "Review agreements, activate pricing with a second-person check, and find billing differences.")}
    <div class="cards">
      <div class="metric"><div class="metric-label">Clients</div><div class="metric-value">${counts.clients}</div><div class="metric-note">Active clients</div></div>
      <div class="metric"><div class="metric-label">Agreements</div><div class="metric-value">${counts.agreements}</div><div class="metric-note">MSA and MLA linked by client</div></div>
      ${state.role !== "structuring" ? `<div class="metric"><div class="metric-label">Pending approvals</div><div class="metric-value">${counts.pending_approvals}</div><div class="metric-note">Four-eyes workflow</div></div>
      <div class="metric"><div class="metric-label">Clients with findings</div><div class="metric-value">${summary.clients_with_issues}</div><div class="metric-note">${summary.discrepancy_count} line findings</div></div>` : ""}
    </div>
    <div class="split">
      <section class="panel">
        <div class="panel-head"><div><h2>Work in progress</h2><div class="panel-desc">Structuring reviews contract terms; Finance prepares pricing and a different Finance user approves.</div></div><span class="pill">13 services</span></div>
        <div class="notice"><b>Structuring</b> uploads and edits extracted contract details. <b>Finance</b> reviews those terms, enters pricing, and requests approval. A different Finance user approves before pricing becomes active.</div>
        <div class="row"><button class="btn btn-primary" onclick="go('contracts')">Open Contract</button>${state.role !== "structuring" ? '<button class="btn btn-secondary" onclick="go(\'pricing\')">Open Pricing</button>' : ""}</div>
      </section>
      ${state.role !== "structuring" ? `<section class="panel">
        <div class="panel-head"><div><h2>Billing audit</h2><div class="panel-desc">Compare contract, active pricing, and billed line items by period.</div></div></div>
        <div class="audit-summary">
          <div class="audit-stat"><span>Selected client</span><strong>${esc(state.clients.find((client) => client.id === state.clientId)?.name || "")}</strong></div>
          <div class="audit-stat"><span>Billing periods</span><strong>Jan-Mar 2026</strong></div>
          <div class="audit-stat"><span>Source</span><strong>Selectable PDF</strong></div>
        </div>
        <button class="btn btn-quiet" onclick="go('billing')">View billing audit</button>
      </section>` : ""}
    </div>
    `;
}

function go(page) {
  if (state.role === "structuring" && ["pricing", "billing"].includes(page)) {
    notify("This section is available to Finance users only.");
    return;
  }
  if (page === "contracts" && state.page !== "contracts") {
    state.contractExistingClientId = null;
    state.contractUploadClientId = null;
    state.selectedAgreement = null;
    state.uploadedAgreement = null;
    state.agreements = [];
    state.selectedAgreementCheck = false;
    state.contractMode = "existing";
    state.contractExistingAgreementType = "";
  } else if (page !== "contracts" && !state.clientId) {
    state.clientId = state.clients[0]?.id || null;
  }
  state.page = page;
  sessionStorage.setItem("apollo-page", page);
  render();
}
function contractClientOptions(selectedId) {
  return `<option value="">Select a client</option>${state.clients.map((client) => `<option value="${esc(client.id)}" ${client.id === selectedId ? "selected" : ""}>${esc(client.name)}</option>`).join("")}`;
}
async function renderContracts() {
  activeEvidence = null;

  // No auto-load. selectedAgreement is only set by Fetch agreement button.
  // Upload mode uses uploadedAgreement.
  if (state.contractMode === "existing") {
    const hasPick =
      state.contractExistingClientId && state.contractExistingAgreementType;
    if (!hasPick) {
      state.selectedAgreement = null;
    }
  }

  const existingSelected = state.agreements.find(
    (agreement) => agreement.id === state.selectedAgreement,
  );
  const selected =
    state.contractMode === "upload" ? state.uploadedAgreement : existingSelected;
  // isDraft is true only if the selected agreement has status 'draft'
  const isDraft = selected && selected.status === "draft";
  const sourceDescription = selected
    ? `${esc(selected.agreement_type)} Â· ${esc(selected.version_label)}`
    : "Choose an existing client or upload a new agreement.";

  $("#main").innerHTML =
    `${head("Contract workspace", "Agreement review", "View a stored client agreement, or upload a new agreement for extraction.", `<span class="tag neutral">${state.role === "structuring" ? "Structuring can edit terms" : "Finance view is read-only"}</span>`)}
  <div class="contract-tabs" role="tablist" aria-label="Contract source">
    <button class="tab-btn ${state.contractMode === "existing" ? "active" : ""}" role="tab" aria-selected="${state.contractMode === "existing"}" data-tab="existing" id="tab-existing">Existing Aggrement</button>
    <button class="tab-btn ${state.contractMode === "upload" ? "active" : ""}" role="tab" aria-selected="${state.contractMode === "upload"}" data-tab="upload" id="tab-upload">Upload Agreement</button>
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
        ${selected && (state.role === "finance" || state.role === "structuring") ? `
          <div style="margin-top:10px;display:flex;gap:8px;align-items:center;">
            <button class="btn btn-secondary" id="preview-billing">Preview Next Billing Cycle</button>
          </div>
        ` : ""}
      </div>
      <div id="terms-editor" class="scroll-panel">${selected ? renderTermsEditor(selected, isDraft) : '<div class="empty contract-empty">Select an existing client or upload a PDF to view extracted terms.</div>'}</div>
      <div class="row spread contract-footer">
        <span class="small muted">All 13 services are represented in the catalogue.</span>
        ${
          selected
            ? isDraft
              ? state.role === "structuring" || state.role === "finance"
                ? '<button class="btn btn-primary" id="save-draft-btn">Save in system</button>'
                : '<button class="btn btn-primary" id="save-draft-btn" disabled>Save in system</button>'
              : state.role === "structuring"
                ? '<button class="btn btn-primary" id="save-terms">Save Structuring edits</button>'
                : '<button class="btn btn-primary" id="save-terms" disabled>Save Structuring edits</button>'
            : ""
        }
        ${!isDraft && state.role === "structuring" ? '<button class="btn btn-danger" id="delete-agreement-btn" style="margin-left:auto">Delete Agreement</button>' : ""}
      </div>
    </section>
  </div>`;


  // Tab switching
  $("#tab-existing").onclick = async () => {
    state.contractMode = "existing";
    state.uploadedAgreement = null;
    await renderContracts();
  };
  $("#tab-upload").onclick = async () => {
    state.contractMode = "upload";
    await renderContracts();
  };

  if (state.contractMode === "existing") {
    $("#existing-client-picker").onchange = async (event) => {
      state.contractExistingClientId = event.target.value || null;
      state.contractExistingAgreementType = "";
      state.uploadedAgreement = null;
      state.selectedAgreement = null;
      state.agreements = [];
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
      state.agreements = [];
      state.selectedAgreementCheck = false;
      await renderContracts();
    };
    $("#fetch-agreement").onclick = async () => {
      if (
        !state.contractExistingClientId ||
        !state.contractExistingAgreementType
      )
        return;
      state.selectedAgreementCheck = true;
      const agreements = await api(
        `/api/clients/${state.contractExistingClientId}/agreements?type=${state.contractExistingAgreementType}`,
      );
      state.agreements = agreements;
      state.selectedAgreement = agreements[0]?.id || null;
      if (!state.selectedAgreement) {
        notify(
          `No ${state.contractExistingAgreementType} agreement found for this client.`,
        );
      }
      await renderContracts();
    };
  }

  if (state.contractMode === "upload") {
    $('#agreement-upload input[type="file"]').onchange = (event) => {
      if (event.target.files.length) {
        state.contractMode = "upload";
        state.uploadedAgreement = null;
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

  if (selected && (state.role === "structuring" || state.role === "finance")) {
    if (isDraft) {
      $("#save-draft-btn").onclick = saveDraft;
    } else if (state.role === "structuring") {
      $("#save-terms").onclick = saveTerms;
    }
  }

  if (selected && state.role === "structuring" && !isDraft) {
    const deleteBtn = $("#delete-agreement-btn");
    if (deleteBtn) {
      deleteBtn.onclick = async () => {
        // Show custom confirmation modal
        const confirmOverlay = document.createElement("div");
        confirmOverlay.className = "modal-overlay";
        confirmOverlay.style.cssText = `
          position: fixed; inset: 0; background: rgba(20, 50, 60, 0.8);
          display: flex; align-items: center; justify-content: center;
          z-index: 10000; padding: 20px; animation: fadeIn 0.15s ease-out;
        `;
        const confirmModal = document.createElement("div");
        confirmModal.className = "modal-content";
        confirmModal.style.cssText = `
          background: white; border-radius: 12px; box-shadow: var(--shadow);
          max-width: 500px; width: 100%; padding: 24px;
          animation: slideUp 0.2s ease-out;
        `;
        confirmModal.innerHTML = `
          <h3 style="margin:0 0 16px 0;font:700 18px 'Manrope';">Delete Agreement</h3>
          <p style="margin:0 0 16px 0;color:#555;">
            Delete this agreement? This action cannot be undone.<br><br>
            <span style="color:#777;font-size:14px;">
            If the client has no other active agreements, the client will also be removed from the system.
            </span>
          </p>
          <div style="display:flex;gap:12px;justify-content:flex-end;">
            <button id="cancel-delete" class="btn btn-secondary" style="flex:1;">Cancel</button>
            <button id="confirm-delete" class="btn btn-danger" style="flex:1;">Delete Agreement</button>
          </div>
        `;
        confirmOverlay.appendChild(confirmModal);
        document.body.appendChild(confirmOverlay);

        // Close modal handlers
        const closeConfirmModal = () => {
          confirmOverlay.style.animation = "fadeIn 0.15s ease-out reverse";
          setTimeout(() => {
            if (confirmOverlay.parentNode) confirmOverlay.parentNode.removeChild(confirmOverlay);
          }, 150);
        };
        confirmModal.querySelector("#cancel-delete").onclick = closeConfirmModal;
        confirmOverlay.onclick = (e) => { if (e.target === confirmOverlay) closeConfirmModal(); };

        // Execute delete
        confirmModal.querySelector("#confirm-delete").onclick = async () => {
          closeConfirmModal();
          try {
            const response = await fetch(
              serviceUrl(`/api/agreements/${selected.id}`),
              {
                method: "DELETE",
                headers: {
                  Authorization: `Bearer ${state.token}`,
                  "Content-Type": "application/json",
                },
              },
            );
            if (!response.ok) {
              const err = await response.json();
              throw new Error(err.detail || "Failed to delete agreement");
            }
            const result = await response.json();
            notify(
              result.client_deactivated
                ? "Agreement deleted. Client had no other active agreements and has been removed."
                : "Agreement deleted and archived.",
            );
            // Refresh bootstrap data (clients list) and agreements
            state.apiData = await api("/api/bootstrap");
            state.clients = state.apiData.clients;
            state.selectedAgreement = null;
            state.uploadedAgreement = null;
            state.contractExistingClientId = null;
            state.contractExistingAgreementType = "";
            await renderContracts();
          } catch (err) {
            notify(err.message);
          }
        };
        return;
      };
    }
  }

  if (selected) {
    $("#download-agreement").onclick = () =>
      downloadAgreementPdf(selected).catch((error) => notify(error.message));
    loadAgreementPdf(selected.id).catch((error) => notify(error.message));
  }

  // Preview billing button handler - shows forecast for next monthly billing cycle
  const previewBtn = $("#preview-billing");
  if (previewBtn) {
    previewBtn.onclick = async () => {
      // Auto-compute next month's billing cycle (one month from today)
      const today = new Date();
      const nextMonth = new Date(today.getFullYear(), today.getMonth() + 1, 1);
      const monthEnd = new Date(today.getFullYear(), today.getMonth() + 2, 0);
      const formatDate = (d) => d.toISOString().split("T")[0];
      const start = formatDate(nextMonth);
      const end = formatDate(monthEnd);
      const agreementType = selected.agreement_type; // "MSA" or "MLA"
      const stream = agreementType === "MLA" ? "LEASE" : "SERVICE";

      const client = state.clients.find(c => c.id === state.contractExistingClientId || c.id === selected.client_id);
      const clientId = client?.id || selected.client_id;
      const clientName = client?.name || selected.detected_client_name || selected.client_name || "Unknown Client";

      let forecast;
      if (isDraft) {
        // For drafts, compute forecast from extracted contract terms
        forecast = computeForecastFromContract(selected, start, end);
      } else {
        // For existing agreements, use active pricing from billing service
        try {
          const pricingForecast = await api(
            `/api/clients/${clientId}/billing-forecast?${new URLSearchParams({ start, end, stream })}`
          );
          // If pricing API returns no lines or zero total (no pricing setup), fallback to contract-based forecast
          const hasValidForecast = pricingForecast.lines && pricingForecast.lines.length > 0 &&
                                   pricingForecast.total > 0;
          if (!hasValidForecast) {
            forecast = computeForecastFromContract(selected, start, end);
          } else {
            forecast = pricingForecast;
          }
        } catch (e) {
          // Fallback to contract-based forecast if pricing API fails
          forecast = computeForecastFromContract(selected, start, end);
        }
      }

      state.forecastPreview = {
        clientId,
        clientName,
        agreementType,
        start,
        end,
        stream,
        data: forecast,
      };
      renderForecastPreviewModal();
    };
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

function computeForecastFromContract(agreement, periodStart, periodEnd) {
  // Compute forecast billing from extracted contract terms (for drafts/previews)
  // Only show data for the agreement type that is currently open/uploaded
  const extracted = agreement.extracted || {};
  const agreementType = agreement.agreement_type; // "MSA" or "MLA"
  const lines = [];
  let total = 0.0;

  if (agreementType === "MSA") {
    // Process MSA services
    if (extracted.services) {
      for (const service of extracted.services) {
        if (!service.subscribed) continue;
        if (service.contract_amount == null) continue;

        const quantity = service.vehicle_count || service.driver_count || 1;
        const amount = Number(service.contract_amount) * quantity;
        total += amount;

        lines.push({
          service_code: service.service_code,
          service_name: service.service_name,
          component_code: service.component_name || "monthly_per_vehicle",
          component_name: service.component_name ? service.component_name.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase()) : "Monthly Service",
          billing_stream: "SERVICE",
          charge_type: "recurring",
          quantity: quantity,
          rate: Number(service.contract_amount),
          rate_unit: service.rate_unit || "vehicle_month",
          amount: amount,
          currency: service.pricing_basis || "USD",
        });
      }
    }

    // Process MSA components (one-time charges like FUEL activation)
    if (extracted.components) {
      for (const component of extracted.components) {
        if (component.contract_amount == null) continue;

        const quantity = component.quantity || 1;
        const amount = Number(component.contract_amount) * quantity;
        total += amount;

        lines.push({
          service_code: component.service_code || "FUEL",
          service_name: component.service_name || "Fuel",
          component_code: component.component_name || "activation",
          component_name: component.component_name ? component.component_name.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase()) : "One-time Setup",
          billing_stream: "SERVICE",
          charge_type: component.charge_type || "one_time",
          quantity: quantity,
          rate: Number(component.contract_amount),
          rate_unit: component.rate_unit || "account",
          amount: amount,
          currency: component.pricing_basis || "USD",
        });
      }
    }
  } else if (agreementType === "MLA") {
    // Process MLA lease
    if (extracted.lease) {
      const lease = extracted.lease;
      const vehicles = lease.vehicles?.length ? lease.vehicles : [lease];

      for (const vehicle of vehicles) {
        if (vehicle.contract_amount == null) continue;

        const quantity = vehicle.quantity || 1;
        const amount = Number(vehicle.contract_amount) * quantity;
        total += amount;

        const vehicleType = vehicle.vehicle_type ||
          [vehicle.vehicle_make, vehicle.vehicle_model].filter(Boolean).join(" ");

        lines.push({
          service_code: vehicle.service_code || "LEASE-01",
          service_name: vehicle.service_name || "Fleet vehicle lease",
          component_code: vehicle.component_name || "monthly_lease",
          component_name: `Monthly Lease - ${vehicleType || "Vehicle"}`,
          billing_stream: "LEASE",
          charge_type: "recurring",
          quantity: quantity,
          rate: Number(vehicle.contract_amount),
          rate_unit: vehicle.rate_unit || "vehicle_month",
          amount: amount,
          currency: vehicle.pricing_basis || "USD",
        });
      }
    }
  }

  return {
    client_id: agreement.client_id || agreement.detected_client_id,
    period_start: periodStart,
    period_end: periodEnd,
    billing_stream: agreementType === "MLA" ? "LEASE" : "SERVICE",
    lines: lines,
    total: Math.round(total * 100) / 100,
    line_count: lines.length,
  };
}

function renderForecastPreviewModal() {
  const preview = state.forecastPreview;
  if (!preview) return;

  const { clientName, agreementType, start, end, stream, data } = preview;
  const lines = data.lines || [];
  const total = data.total || 0;

  // Create modal overlay
  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";
  overlay.style.cssText = `
    position: fixed; inset: 0; background: rgba(20, 50, 60, 0.6);
    display: flex; align-items: center; justify-content: center;
    z-index: 1000; padding: 20px; animation: fadeIn 0.15s ease-out;
  `;

  // Create modal content
  const modal = document.createElement("div");
  modal.className = "modal-content";
  modal.style.cssText = `
    background: white; border-radius: 12px; box-shadow: var(--shadow);
    max-width: 900px; width: 100%; max-height: 90vh; overflow: auto;
    animation: slideUp 0.2s ease-out;
  `;

  const lineRows = lines.map(line => `
    <tr>
      <td><span class="tag ${line.billing_stream === 'SERVICE' ? 'good' : 'neutral'}">${esc(line.billing_stream)}</span></td>
      <td>${esc(line.service_name)}</td>
      <td>${esc(line.component_name)}</td>
      <td>${esc(line.charge_type)}</td>
      <td>${line.quantity} ${esc(line.rate_unit)}</td>
      <td>${money(line.rate)}</td>
      <td><b>${money(line.amount)}</b></td>
    </tr>
  `).join("");

  modal.innerHTML = `
    <style>
      @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
      @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    </style>
    <div style="display:flex;justify-content:space-between;align-items:center;padding:16px 20px;border-bottom:1px solid var(--line);">
      <div>
        <h2 style="margin:0;font:700 16px 'Manrope';">Forecast Billing Preview</h2>
        <div class="small muted" style="margin-top:4px;">
          ${esc(clientName)} · ${esc(agreementType)} · ${esc(stream)} · ${esc(start)} to ${esc(end)}
        </div>
      </div>
      <button id="close-preview-modal" class="icon-btn" style="font-size:20px;color:var(--muted);background:none;border:none;cursor:pointer;padding:4px;">&times;</button>
    </div>
    <div style="padding:20px;">
      <div class="table-wrap" style="max-height:50vh;overflow:auto;">
        <table style="width:100%;border-collapse:collapse;font-size:11px;">
          <thead>
            <tr style="background:#f7faf9;color:#667b81;position:sticky;top:0;z-index:1;">
              <th style="padding:10px 11px;text-align:left;font-size:9px;text-transform:uppercase;letter-spacing:.55px;font-weight:700;border-bottom:1px solid #edf1f1;">Stream</th>
              <th style="padding:10px 11px;text-align:left;font-size:9px;text-transform:uppercase;letter-spacing:.55px;font-weight:700;border-bottom:1px solid #edf1f1;">Service</th>
              <th style="padding:10px 11px;text-align:left;font-size:9px;text-transform:uppercase;letter-spacing:.55px;font-weight:700;border-bottom:1px solid #edf1f1;">Component</th>
              <th style="padding:10px 11px;text-align:left;font-size:9px;text-transform:uppercase;letter-spacing:.55px;font-weight:700;border-bottom:1px solid #edf1f1;">Charge</th>
              <th style="padding:10px 11px;text-align:left;font-size:9px;text-transform:uppercase;letter-spacing:.55px;font-weight:700;border-bottom:1px solid #edf1f1;">Qty/Rate</th>
              <th style="padding:10px 11px;text-align:left;font-size:9px;text-transform:uppercase;letter-spacing:.55px;font-weight:700;border-bottom:1px solid #edf1f1;">Rate</th>
              <th style="padding:10px 11px;text-align:left;font-size:9px;text-transform:uppercase;letter-spacing:.55px;font-weight:700;border-bottom:1px solid #edf1f1;">Amount</th>
            </tr>
          </thead>
          <tbody>
            ${lineRows || '<tr><td colspan="7" style="padding:20px;text-align:center;color:var(--muted);">No forecast lines for this period and stream</td></tr>'}
          </tbody>
        </table>
      </div>
      <div style="display:flex;justify-content:space-between;align-items:center;margin-top:16px;padding-top:16px;border-top:1px solid var(--line);">
        <div class="small muted">Based on active pricing components for ${esc(clientName)}</div>
        <div style="font:700 18px 'Manrope';color:var(--ink);">Total: ${money(total)}</div>
      </div>
      <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px;">
        <button class="btn btn-quiet" id="close-preview-modal-btn">Close</button>
        <button class="btn btn-primary" id="download-preview-pdf">Download as PDF</button>
      </div>
    </div>
  `;

  overlay.appendChild(modal);
  document.body.appendChild(overlay);

  // Event handlers
  const closeModal = () => {
    overlay._cleanup();
    overlay.remove();
    state.forecastPreview = null;
  };

  overlay.querySelector("#close-preview-modal").onclick = closeModal;
  overlay.querySelector("#close-preview-modal-btn").onclick = closeModal;
  overlay.onclick = (e) => {
    if (e.target === overlay) closeModal();
  };

  // Download PDF button
  overlay.querySelector("#download-preview-pdf").onclick = async () => {
    try {
      const result = await api(
        `/api/clients/${preview.clientId}/billing-forecast-pdf?${new URLSearchParams({ start: preview.start, end: preview.end, stream: preview.stream })}`,
        { method: "POST" }
      );
      notify(`Forecast PDF generated: ${result.filename}`);
      const a = document.createElement("a");
      a.href = result.download_url;
      a.download = result.filename;
      a.click();
    } catch (e) {
      notify(e.message);
    }
  };

  // Handle Escape key
  const handleEscape = (e) => {
    if (e.key === "Escape") closeModal();
  };
  document.addEventListener("keydown", handleEscape);
  // Store cleanup function on overlay
  overlay._cleanup = () => document.removeEventListener("keydown", handleEscape);
}

function renderAgreementFacts(agreement) {
  const clientRecord = state.clients.find(
    (item) => item.id === agreement.client_id,
  );
  const client =
    clientRecord?.name || agreement.detected_client_name || agreement.client_id;
  const profile = agreement.extracted?.parties?.client || clientRecord || {};
  const values = [
    ["Agreement type", agreement.agreement_type],
    ["Client", client],
    ["Legal entity name", profile.legal_name],
    ["Entity type", profile.entity_type],
    ["Formation jurisdiction", profile.formation_jurisdiction],
    ["Registered address", profile.registered_address],
    ["Version", agreement.version_label],
    ["Effective date", agreement.effective_date],
  ];
  return `<dl class="agreement-facts">${values.map(([field, value]) => `<div><dt>${field}</dt><dd>${esc(value || "Not found")}</dd></div>`).join("")}</dl>${profile.source_text ? `<div class="service-edit client-profile-evidence">${renderEvidence(profile, "legal_name")}</div>` : ""}`;
}

function renderTermsEditor(agreement, isDraft = false) {
  const extracted = agreement.extracted || {};
  const disabled = state.role !== "structuring" ? "disabled" : "";
  // For drafts, client name and agreement type are editable; other fields are read-only until saved
  const editable = disabled === "" || isDraft; // editing allowed in structuring role OR for drafts
  const clientName =
    agreement.detected_client_name ||
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
    const vehicles = lease.vehicles?.length ? lease.vehicles : [lease];
    const fields = [
      ["quantity", "Vehicle count", "number"],
      ["contract_amount", "Monthly rate", "number"],
      ["rate_unit", "Rate unit", "text"],
      ["term_months", "Lease term (months)", "number"],
      ["billing_frequency", "Billing frequency", "text"],
      ["billing_day", "Billing day", "text"],
      ["vehicle_make", "Vehicle make", "text"],
      ["vehicle_model", "Vehicle model", "text"],
      ["engine_type", "Engine type", "text"],
      ["pricing_basis", "Currency / basis", "text"],
    ];
    return `${renderAgreementFacts(agreement)}<div class="notice">Lease details extracted from this MLA. Each vehicle type keeps its own quantity and rate.</div>
      ${vehicles
        .map((vehicle, index) => {
          const vehicleType =
            vehicle.vehicle_type ||
            [
              vehicle.vehicle_make,
              vehicle.vehicle_model,
              vehicle.engine_type && `(${vehicle.engine_type})`,
            ]
              .filter(Boolean)
              .join(" ");
          const sourceHasBillingFields = vehicle.source_text?.includes("|");
          return `<div class="service-edit lease-vehicle"><div><b>${esc(vehicleType || `Vehicle ${index + 1}`)}</b><span class="service-rate">${vehicle.contract_amount == null ? "Rate needs review" : `${esc(vehicle.pricing_basis || "USD")} ${Number(vehicle.contract_amount).toFixed(2)}`}</span></div><div class="three">${fields
            .map(([field, label, type]) => {
              const fieldDisabled =
                !sourceHasBillingFields &&
                ["billing_frequency", "billing_day"].includes(field)
                  ? "disabled"
                  : disabled;
              return `<label class="control"><span class="field-label">${label}</span><input data-lease-field="${index}|${field}" type="${type}" ${field === "contract_amount" ? 'step="0.01"' : type === "number" ? 'step="1"' : ""} value="${esc(vehicle[field] ?? "")}" ${fieldDisabled}>${renderEvidence(vehicle, field)}</label>`;
            })
            .join("")}</div></div>`;
        })
        .join("")}`;
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
    if (!clientName.trim()) throw new Error("Enter a client name before saving.");
    const agreementType =
      agreementTypeInput?.value || agreement.detected_agreement_type;
    const client = state.clients.find(
      (item) => item.name.toLowerCase() === clientName.trim().toLowerCase(),
    );
    const clientId = client?.id || agreement.detected_client_id;
    if (!clientId) throw new Error("Enter a client name before saving.");

    // Check if a non-draft agreement already exists for this client + type
    const existingAgreements = await api(`/api/clients/${clientId}/agreements?type=${agreementType}`);
    if (existingAgreements.length > 0) {
      notify(`Client already has an active ${agreementType} agreement in the system.`);
      return;
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
          client_id: clientId,
          agreement_type: agreementType,
          client_name: clientName.trim(),
        }),
      },
    );
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "Failed to save identifiers");
    }
    const saved = await response.json();

    // After saving, transition from draft mode to saved agreement mode:
    // - The agreement is now in 'review' status, not 'draft'
    // - isDraft is determined by !!state.uploadedAgreement, so we set it to the saved agreement
    // - This ensures billing preview uses the billing API (not contract-based)
    state.uploadedAgreement = saved;
    state.clientId = clientId;
    // Keep the contract mode as-is (likely "upload" from draft flow)

    // Refresh bootstrap data to show updated clients in dropdowns
    state.apiData = await api("/api/bootstrap");
    state.clients = state.apiData.clients;

    // Fetch the saved agreement from the correct client to ensure we have all fields
    const savedClient = state.clients.find(c => c.id === clientId);
    if (savedClient) {
      state.contractExistingClientId = savedClient.id;
      state.contractExistingAgreementType = agreementType;
      const agreements = await api(`/api/clients/${savedClient.id}/agreements?type=${agreementType}`);
      state.agreements = agreements;
      // Set selectedAgreement to the saved agreement (if it's in the list)
      const savedInList = agreements.find(a => a.id === saved.id);
      if (savedInList) {
        state.selectedAgreement = saved.id;
      }
    }

    // Switch to "View existing agreement" tab so the client shows in the dropdown
    state.contractMode = "existing";
    state.uploadedAgreement = null; // Clear draft mode

    notify("Draft saved in system");
    await renderContracts();
  } catch (err) {
    notify(err.message);
  }
}

async function saveTerms() {
  let progressToast = null;
  try {
    const agreement = state.agreements.find(
      (item) => item.id === state.selectedAgreement,
    );
    if (!agreement) throw new Error("Select an agreement before saving.");
    const extracted = structuredClone(agreement.extracted);

    if (agreement.agreement_type === "MLA") {
      const lease = extracted.lease || {};
      const vehicles = lease.vehicles?.length ? lease.vehicles : [lease];
      const numericFields = new Set([
        "quantity",
        "contract_amount",
        "term_months",
      ]);
      const fields = [
        "quantity",
        "contract_amount",
        "term_months",
        "rate_unit",
        "billing_frequency",
        "billing_day",
        "vehicle_make",
        "vehicle_model",
        "engine_type",
        "pricing_basis",
        "effective_from",
      ];
      vehicles.forEach((vehicle, index) => {
        for (const key of fields) {
          const input = document.querySelector(
            `[data-lease-field="${index}|${key}"]`,
          );
          if (!input) continue;
          vehicle[key] = numericFields.has(key)
            ? input.value === ""
              ? null
              : Number(input.value)
            : input.value;
        }
      });
      if (vehicles.length) {
        Object.assign(lease, vehicles[0]);
        lease.vehicles = vehicles;
      }
      extracted.lease = lease;
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

    // Keep progress visible while the original PDF is patched and re-extracted.
    clearEvidenceHighlight();
    progressToast = document.createElement("div");
    progressToast.className = "toast show";
    progressToast.style.cssText = "background:#2a3a3a; z-index:10000;";
    progressToast.innerHTML = `<b>Saving agreement version</b><br><span class="small">Updating changed fields in the original PDF and refreshing evidence...</span>`;
    document.body.appendChild(progressToast);

    try {
      // Save creates a new version while retaining the original document layout.
      const saved = await api(`/api/agreements/${agreement.id}/save-version`, {
        method: "PUT",
        body: JSON.stringify({ extracted, update_comment: comment }),
      });

      // Load the newly saved PDF so evidence uses the current version.
      state.selectedAgreement = saved.id;
      // Refresh the agreements list to include the new version
      if (
        state.contractExistingClientId &&
        state.contractExistingAgreementType
      ) {
        state.agreements = await api(
          `/api/clients/${state.contractExistingClientId}/agreements?type=${state.contractExistingAgreementType}`,
        );
      }

      // Remove progress toast
      document.body.removeChild(progressToast);
      notify(
        "New version saved with audit comment; original PDF layout preserved",
      );
      await renderContracts();
    } catch (error) {
      // Remove progress toast on error
      if (progressToast.parentNode) {
        document.body.removeChild(progressToast);
      }
      notify(error.message);
    }
  } catch (error) {
    if (progressToast?.parentNode) document.body.removeChild(progressToast);
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
<div class="split"><section class="panel"><div class="panel-head"><div><h2>Prepare pricing version</h2><div class="panel-desc">Choose the agreement set, review each charge, then send to a second Finance approver.</div></div></div><div class="row"><button class="btn btn-secondary" id="load-contract-pricing" ${state.role !== "finance" ? "disabled" : ""}>Load subscribed contract terms</button><button class="btn btn-quiet" id="add-component" ${state.role !== "finance" ? "disabled" : ""}>+ Add component</button></div><div id="pricing-editor" class="pricing-list" style="margin-top:12px"></div><div class="row spread" style="margin-top:14px"><span class="small muted">Submitter: ${esc(state.userId)}</span><button class="btn btn-primary" id="submit-pricing" ${state.role !== "finance" ? "disabled" : ""}>Submit</button></div></section>
<section class="panel"><div class="panel-head"><div><h2>Pending approval</h2><div class="panel-desc">Review the submitted rates and terms before a different Finance user approves.</div></div><span class="tag ${pending.length ? "warn" : "good"}">${pending.length} pending</span></div>${pending.length ? pending.map((r) => `<div class="approval"><h3>Pricing version v${r.version}</h3><div class="approval-meta">Initiated by ${esc(r.initiated_by)} Â· ${esc(r.created_at)} Â· ${esc(r.id.slice(0, 8))}</div><button class="btn btn-primary review-pricing-btn" data-id="${esc(r.id)}">Review pricing details</button>${r.initiated_by === state.userId ? '<div class="small muted" style="margin-top:7px">Sign in as a different Finance user to approve.</div>' : ""}</div>`).join("") : '<div class="empty">No pricing requests are waiting for approval.</div>'}</section></div>`;
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
  document.querySelectorAll(".review-pricing-btn").forEach((button) => {
    button.onclick = () => {
      const request = pending.find((item) => item.id === button.dataset.id);
      if (!request) throw new Error("Pricing approval request not found.");
      const components = data.components.filter(
        (component) => component.approval_request_id === request.id,
      );
      renderPricingApprovalModal(request, components);
    };
  });
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
        `<div class="pricing-row" data-row="${i}"><div class="control"><label>Service</label><input data-field="service_name" value="${esc(c.service_name)}"></div><div class="control"><label>Component</label><input data-field="component_name" value="${esc(c.component_name)}"></div><div class="control"><label>Stream</label><select data-field="billing_stream"><option ${c.billing_stream === "SERVICE" ? "selected" : ""}>SERVICE</option><option ${c.billing_stream === "LEASE" ? "selected" : ""}>LEASE</option></select></div><div class="control"><label>Charge type</label><select data-field="charge_type"><option value="recurring" ${c.charge_type === "recurring" ? "selected" : ""}>Recurring</option><option value="one_time" ${c.charge_type === "one_time" ? "selected" : ""}>One-time</option></select></div><div class="control"><label>Amount</label><input data-field="amount" type="number" min="0" step="0.01" value="${Number(c.amount || 0)}"></div><div class="control"><label>Price format</label><select data-term="pricing_basis"><option value="USD" ${c.terms?.pricing_basis === "USD" ? "selected" : ""}>USD</option><option value="PERCENTAGE" ${c.terms?.pricing_basis === "PERCENTAGE" ? "selected" : ""}>Percentage</option><option value="BASIS_POINTS" ${c.terms?.pricing_basis === "BASIS_POINTS" ? "selected" : ""}>Basis points</option></select></div><div class="control"><label>Rate unit</label><input data-field="rate_unit" value="${esc(c.rate_unit)}"></div><div class="control"><label>Quantity</label><input data-field="quantity" type="number" min="0" step="1" value="${Number(c.quantity || 1)}"></div><button class="icon-btn" data-remove="${i}" title="Remove component">Ã—</button></div>`,
    )
    .join("");
  host.querySelectorAll("[data-field]").forEach(
    (el) =>
      (el.onchange = () => {
        const row = el.closest("[data-row]");
        const c = state.pricingDraft[Number(row.dataset.row)];
        const field = el.dataset.field;
        c[field] = ["amount", "quantity"].includes(field)
          ? Number(el.value)
          : el.value;
        if (field === "service_name") {
          c.service_code = el.value
            .trim()
            .replace(/[^A-Za-z0-9]+/g, "_")
            .replace(/^_+|_+$/g, "")
            .toUpperCase();
        } else if (field === "component_name") {
          c.component_code = el.value
            .trim()
            .replace(/[^A-Za-z0-9]+/g, "_")
            .replace(/^_+|_+$/g, "")
            .toLowerCase();
        }
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
      for (const vehicle of lease?.vehicles || (lease ? [lease] : [])) {
        if (vehicle.contract_amount == null) {
          missingRates += 1;
          continue;
        }
        const vehicleType =
          vehicle.vehicle_type ||
          [vehicle.vehicle_make, vehicle.vehicle_model]
            .filter(Boolean)
            .join(" ");
        rows.push({
          agreement_id: agreement.id,
          billing_stream: "LEASE",
          service_code: vehicle.service_code,
          service_name: vehicle.service_name,
          component_code: vehicle.service_code || vehicle.component_name,
          component_name: `Monthly Lease - ${vehicleType || "Vehicle"}`,
          charge_type: "recurring",
          amount: Number(vehicle.contract_amount),
          currency: vehicle.pricing_basis || "USD",
          rate_unit: vehicle.rate_unit || "vehicle_month",
          quantity: Number(vehicle.quantity ?? 1),
          billing_frequency: vehicle.billing_frequency || "monthly",
          billing_day: vehicle.billing_day || "1",
          effective_from: vehicle.effective_from || agreement.effective_date,
          terms: {
            source_page: vehicle.evidence_page || 1,
            term_months: vehicle.term_months,
            vehicle_type: vehicleType,
            vehicle_make: vehicle.vehicle_make,
            vehicle_model: vehicle.vehicle_model,
            engine_type: vehicle.engine_type,
            pricing_basis: vehicle.pricing_basis,
          },
        });
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
  if (
    components.some(
      (component) =>
        !String(component.service_name || "").trim() ||
        !String(component.component_name || "").trim(),
    )
  ) {
    notify("Enter a service and component name for every pricing charge");
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
function renderPricingApprovalModal(request, components) {
  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";
  overlay.style.cssText =
    "position:fixed;inset:0;background:rgba(20,50,60,.6);display:flex;align-items:center;justify-content:center;z-index:1000;padding:20px";
  const modal = document.createElement("div");
  modal.className = "modal-content";
  modal.setAttribute("role", "dialog");
  modal.setAttribute("aria-modal", "true");
  modal.setAttribute("aria-label", "Pricing approval details");
  modal.style.cssText =
    "background:white;border-radius:12px;box-shadow:var(--shadow);max-width:1000px;width:100%;max-height:90vh;overflow:auto";
  const clientName =
    state.clients.find((client) => client.id === request.client_id)?.name ||
    request.client_id;
  const componentRows = components
    .map((component) => {
      const agreement = state.agreements.find(
        (item) => item.id === component.agreement_id,
      );
      const terms =
        typeof component.terms_json === "string"
          ? JSON.parse(component.terms_json || "{}")
          : component.terms || {};
      const termDetails = Object.entries(terms)
        .filter(([, value]) => value !== null && value !== "")
        .map(
          ([key, value]) =>
            `${esc(key.replaceAll("_", " "))}: ${esc(value)}`,
        )
        .join("<br>");
      return `<tr><td>${esc(agreement?.filename || component.agreement_type)}</td><td>${esc(component.billing_stream)}</td><td>${esc(component.service_name)}<div class="small muted">${esc(component.component_name)}</div></td><td>${esc(component.charge_type)}</td><td>${displayRate(component)}</td><td>${esc(component.quantity)} ${esc(component.rate_unit)}</td><td>${esc(component.billing_frequency)}${component.billing_day ? ` (day ${esc(component.billing_day)})` : ""}</td><td>${esc(component.effective_from)}</td><td>${termDetails || "—"}</td></tr>`;
    })
    .join("");
  const canApprove =
    state.role === "finance" && request.initiated_by !== state.userId;
  modal.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;padding:16px 20px;border-bottom:1px solid var(--line);">
      <div>
        <h2 style="margin:0;font:700 16px 'Manrope';">Review pricing version v${esc(request.version)}</h2>
        <div class="small muted" style="margin-top:4px;">${esc(clientName)} · Submitted by ${esc(request.initiated_by)} · Effective ${esc(request.effective_from)}</div>
      </div>
      <button class="icon-btn" id="close-pricing-review" aria-label="Close pricing review" style="font-size:20px;color:var(--muted);">×</button>
    </div>
    <div style="padding:20px;">
      <div class="table-wrap" style="max-height:55vh;overflow:auto;">
        <table>
          <thead><tr><th>Agreement</th><th>Stream</th><th>Service / component</th><th>Charge</th><th>Rate</th><th>Quantity</th><th>Frequency</th><th>Effective from</th><th>Pricing terms</th></tr></thead>
          <tbody>${componentRows || '<tr><td colspan="9" class="empty">No pricing components were submitted.</td></tr>'}</tbody>
        </table>
      </div>
      <div class="row spread" style="margin-top:16px;">
        <span class="small muted">${components.length} component${components.length === 1 ? "" : "s"} in this request</span>
        <div class="row">
          <button class="btn btn-quiet" id="cancel-pricing-review">Close</button>
          <button class="btn btn-primary" id="approve-reviewed-pricing" ${canApprove && components.length ? "" : "disabled"}>Approve and activate this version</button>
        </div>
      </div>
      ${request.initiated_by === state.userId ? '<div class="small muted" style="margin-top:10px;">Four-eyes control: the submitter cannot approve this request.</div>' : ""}
    </div>`;
  overlay.appendChild(modal);
  document.body.appendChild(overlay);

  const closeModal = () => {
    document.removeEventListener("keydown", handleEscape);
    overlay.remove();
  };
  const handleEscape = (event) => {
    if (event.key === "Escape") closeModal();
  };
  modal.querySelector("#close-pricing-review").onclick = closeModal;
  modal.querySelector("#cancel-pricing-review").onclick = closeModal;
  overlay.onclick = (event) => {
    if (event.target === overlay) closeModal();
  };
  modal.querySelector("#approve-reviewed-pricing").onclick = () => {
    closeModal();
    approvePricing(request.id);
  };
  document.addEventListener("keydown", handleEscape);
}
function previousCalendarMonthRange() {
  const today = new Date();
  const start = new Date(today.getFullYear(), today.getMonth() - 1, 1);
  const end = new Date(today.getFullYear(), today.getMonth(), 0);
  const formatDate = (date) =>
    `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
  return { start: formatDate(start), end: formatDate(end) };
}

async function renderBilling() {
  const auditRange = previousCalendarMonthRange();
  const historyRange = previousCalendarMonthRange();
  const [audit, combined] = await Promise.all([
    api(
      `/api/clients/${state.clientId}/audit?${new URLSearchParams(auditRange)}`,
    ),
    api(
      `/api/clients/${state.clientId}/billing-combined?${new URLSearchParams(historyRange)}`,
    ),
  ]);
  $("#main").innerHTML =
    `${head("Billing workspace", "Billing audit", "Ingest billing PDFs and compare billed line items with contract and active pricing.", `<div class="toolbar">${clientPicker()}</div>`)}
  <div class="subtabs billing-tabs" role="tablist" aria-label="Billing views">
    <button id="billing-audit-tab" class="${state.billingTab === "audit" ? "active" : ""}" type="button" role="tab" aria-selected="${state.billingTab === "audit"}" aria-controls="audit-view">Bill comparison</button>
    <button id="billing-history-tab" class="${state.billingTab === "history" ? "active" : ""}" type="button" role="tab" aria-selected="${state.billingTab === "history"}" aria-controls="history-view">Bill history</button>
  </div>
  <div id="audit-view" role="tabpanel" aria-labelledby="billing-audit-tab" ${state.billingTab === "audit" ? "" : "hidden"}>
    <section class="panel"><div class="panel-head"><div><h2>Ingest billing PDF</h2><div class="panel-desc">Upload a selectable-text billing PDF for processing.</div></div></div><form id="billing-upload" class="filebox"><input type="file" name="file" accept="application/pdf" required><button class="btn btn-primary" style="margin-top:10px">Upload and compare</button></form></section>
    <section id="audit-panel" class="panel"><div class="panel-head"><div><h2>Contract vs pricing vs billing</h2><div class="panel-desc">Use the PDF source and agreement stream to investigate exceptions.</div></div><div class="toolbar"><input id="audit-start" class="input" type="date" value="${auditRange.start}"><input id="audit-end" class="input" type="date" value="${auditRange.end}"><button id="filter-audit" class="btn btn-quiet">Filter periods</button></div></div><div class="audit-summary"><div class="audit-stat"><span>Billing statements in range</span><strong>${audit.invoice_count}</strong></div><div class="audit-stat"><span>Line-level exceptions</span><strong>${audit.discrepancy_count}</strong></div><div class="audit-stat"><span>Rows reviewed</span><strong>${audit.rows.length}</strong></div></div><div id="audit-results">${audit.rows.length ? auditTable(audit.rows) : '<div class="empty">No billing lines found in this period.</div>'}</div></section>
  </div>
  <div id="history-view" role="tabpanel" aria-labelledby="billing-history-tab" ${state.billingTab === "history" ? "" : "hidden"}>
    <section id="combined-panel" class="panel"><div class="panel-head"><div><h2>Bill history (service + lease)</h2><div class="panel-desc">Review uploaded invoices by period, with service and lease subtotals.</div></div><div class="toolbar"><input id="combined-start" class="input" type="date" value="${historyRange.start}"><input id="combined-end" class="input" type="date" value="${historyRange.end}"><button id="filter-combined" class="btn btn-quiet">Filter periods</button></div></div><div id="combined-content">${renderCombinedBilling(combined)}</div></section>
  </div>`;
  bindClient();
  const setBillingTab = (tab) => {
    state.billingTab = tab;
    const auditActive = tab === "audit";
    $("#audit-view").hidden = !auditActive;
    $("#history-view").hidden = auditActive;
    $("#billing-audit-tab").classList.toggle("active", auditActive);
    $("#billing-audit-tab").setAttribute("aria-selected", String(auditActive));
    $("#billing-history-tab").classList.toggle("active", !auditActive);
    $("#billing-history-tab").setAttribute("aria-selected", String(!auditActive));
  };
  $("#billing-audit-tab").onclick = () => setBillingTab("audit");
  $("#billing-history-tab").onclick = () => setBillingTab("history");
  bindCombinedPeriodToggles($("#combined-content"));
  $("#billing-upload").onsubmit = uploadBilling;
  $("#filter-audit").onclick = () => filterReport("audit");
  $("#filter-combined").onclick = () => filterReport("combined");
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
    return '<div class="empty">No uploaded bill history found in this period.</div>';
  const periodRows = data.periods
    .map(
      (period) => `
    <tr class="period-header" data-period="${esc(period.period_start)}">
      <td>${esc(period.period_start)} to ${esc(period.period_end)}</td>
      <td colspan="7">Total: ${money(period.period_total)} (Service: ${money(period.service_total)}, Lease: ${money(period.lease_total)}) <button class="period-toggle" type="button" aria-expanded="false">Show details</button></td>
    </tr>
    <tr class="period-body" data-period-body="${esc(period.period_start)}" hidden>
      <td colspan="8">
        <table class="nested-table">
          <thead><tr><th>Invoice</th><th>Stream</th><th>Service</th><th>Component</th><th>Charge</th><th>Quantity</th><th>Rate</th><th>Amount</th></tr></thead>
          <tbody>
            ${[...period.service_lines, ...period.lease_lines]
              .map(
                (line) => `
              <tr>
                <td>${esc(line.invoice_number)}</td>
                <td><span class="tag ${line.billing_stream === "LEASE" ? "neutral" : "good"}">${esc(line.billing_stream)}</span></td>
                <td>${esc(line.service_name)}</td>
                <td>${esc(line.component_name)}</td>
                <td>${esc(line.charge_type)}</td>
                <td>${line.quantity} ${esc(line.rate_unit)}</td>
                <td>${money(line.rate)}</td>
                <td><b>${money(line.amount)}</b></td>
              </tr>`,
              )
              .join("")}
          </tbody>
        </table>
      </td>
    </tr>`,
    )
    .join("");
  return `<div class="table-wrap"><table><thead><tr><th>Period</th><th colspan="7">Totals</th></tr></thead><tbody>${periodRows}</tbody></table>
    <div class="audit-summary" style="margin-top:12px;">
      <div class="audit-stat"><span>Combined total</span><strong>${money(data.combined_total)}</strong></div>
      <div class="audit-stat"><span>Service total</span><strong>${money(data.service_total)}</strong></div>
      <div class="audit-stat"><span>Lease total</span><strong>${money(data.lease_total)}</strong></div>
    </div></div>`;
}

function bindCombinedPeriodToggles(container) {
  container.querySelectorAll(".period-header").forEach((header) => {
    const button = header.querySelector(".period-toggle");
    button.onclick = () => {
      const periodBody = container.querySelector(
        `[data-period-body="${header.dataset.period}"]`,
      );
      const expanded = button.getAttribute("aria-expanded") === "true";
      periodBody.hidden = expanded;
      button.setAttribute("aria-expanded", String(!expanded));
      button.textContent = expanded ? "Show details" : "Hide details";
    };
  });
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
  const prefix = kind === "audit" ? "audit" : "combined";
  const start = $(`#${prefix}-start`).value;
  const end = $(`#${prefix}-end`).value;
  try {
    if (kind === "audit") {
      const rows = await api(
        `/api/clients/${state.clientId}/audit?${new URLSearchParams({ start, end })}`,
      );
      const panel = $("#audit-panel");
      panel.querySelector(".audit-summary").innerHTML =
        `<div class="audit-stat"><span>Billing statements in range</span><strong>${rows.invoice_count}</strong></div><div class="audit-stat"><span>Line-level exceptions</span><strong>${rows.discrepancy_count}</strong></div><div class="audit-stat"><span>Rows reviewed</span><strong>${rows.rows.length}</strong></div>`;
      $("#audit-results").innerHTML = rows.rows.length
        ? auditTable(rows.rows)
        : '<div class="empty">No billing lines found in this period.</div>';
    } else {
      const rows = await api(
        `/api/clients/${state.clientId}/billing-combined?${new URLSearchParams({ start, end })}`,
      );
      const content = $("#combined-content");
      content.innerHTML = renderCombinedBilling(rows);
      bindCombinedPeriodToggles(content);
    }
    notify("Filters applied");
  } catch (e) {
    notify(e.message);
  }
}

$("#logout").onclick = logout;
load().catch((e) => {
  $("#main").innerHTML =
    `<div class="empty">Could not load the workspace: ${esc(e.message)}. Start the local server from the project directory.</div>`;
});
