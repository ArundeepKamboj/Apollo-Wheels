# UI scenarios and edge-case inventory

Playwright cases in `ui_workflows.spec.js` automate the primary UI paths. Keep this checklist for detailed exploratory/browser acceptance; mark each case in the demo run record after running it.

| ID | Scenario | Expected result |
|---|---|---|
| UI-01 | Open workspace with services available | Overview, client, four workflow links, synthetic-data notice, and audit summary render. |
| UI-02 | API bootstrap fails or returns malformed response | A readable recoverable message appears; no uncaught empty page. |
| UI-03 | Navigate each sidebar item and return | Correct page content and active navigation state render. |
| UI-04 | Switch client in each page | Data refreshes for selected client; stale agreement/pricing draft selection is cleared. |
| UI-05 | Enter Contract review with no client selected, then select a client and an MSA or MLA | Client and terms are blank initially; selecting the client loads its first agreement and corresponding source PDF/terms. Selecting another agreement switches both panels. |
| UI-06 | Structuring opens terms | Save control is enabled; subscribed flags and editable fields are available. |
| UI-07 | Finance opens terms | Values and evidence are visible; edit/save control is disabled. |
| UI-08 | Edit/save one MSA field as Structuring | Saved value remains after reloading agreement. |
| UI-09 | Choose a client, upload MSA and MLA PDFs with Auto-detect and with matching upfront selections | Contract service identifies MSA/MLA from PDF text, reports the detected type, then shows rendered PDF pages beside named extracted fields and values. |
| UI-10 | Select MSA but upload MLA (or the reverse), or upload non-PDF, wrong magic, corrupt, oversized, or ambiguous PDF | A mismatch names the detected type; invalid or ambiguous files show an error; no unusable agreement is added. |
| UI-11 | Hover or keyboard-focus an extracted field with source evidence | The left PDF scrolls to the cited page and highlights the matching source text. |
| UI-12 | Structuring visits Pricing | Setup and approval controls remain Finance-only. |
| UI-13 | Finance loads contract pricing | Every subscribed service and supported one-time component is shown; missing rates are called out. |
| UI-14 | Finance edits/adds/removes a pricing component | Field value and totals/draft state update without loss on ordinary rerender. |
| UI-15 | Submit empty/invalid pricing | Request is rejected with a visible message and no pending version is created. |
| UI-16 | Finance submits valid pricing | New pending version is shown with initiator and version. |
| UI-17 | Initiator tries to approve | Approval is disabled in UI and rejected by service if called directly. |
| UI-18 | Different Finance user approves | Pricing activates, prior version becomes history, and active table refreshes. |
| UI-19 | Repeat approval or approve unknown request | Visible error; active pricing remains unchanged. |
| UI-20 | Upload valid service billing PDF | Invoice and normalized lines appear in history; audit refreshes. |
| UI-21 | Upload lease PDF | LEASE stream stays distinguishable from SERVICE. |
| UI-22 | Upload invalid/unsupported/corrupt billing PDF | Clear error appears; no partial invoice or lines remain. |
| UI-23 | Select date range with matching invoices | Audit/history refresh to matching periods and counts. |
| UI-24 | Select range with no matches | Empty-state text appears without a stale previous table. |
| UI-25 | Filter using start after end or partial range | Inputs are handled predictably; visible validation or a clear empty result. **Policy decision needed:** inclusive/overlap behavior. |
| UI-26 | Review RR mismatch row | Contract, configured, and billed rates and a clear discrepancy explanation appear. |
| UI-27 | Review missing price/billing and unsupported billed service | Each row explains the particular missing/extra condition. |
| UI-28 | Open stored billing PDF from PDF listing or use the Contract review download action | Correct original PDF is returned; contract PDF is embedded for scrolling and only downloads after the explicit Download PDF action; missing file gives clear not-found response. |
| UI-29 | Structuring changes invoice-history preference | Toggle is disabled and server rejects mutation. |
| UI-30 | Finance changes invoice-history preference | Toggle state persists after navigating away and back. |
| UI-31 | Use narrow viewport and keyboard navigation | Content remains reachable, labels/buttons are operable, focus is visible, and tables remain usable. |
| UI-32 | API times out during upload/save/approve/filter | Error is visible; no false success is shown; retry does not duplicate a completed action. **Known gap:** idempotent retry is not implemented. |

UI-11, UI-25 and UI-32 are intentionally retained as acceptance tests even though they expose documented current limitations or unresolved behavior.
