/**
 * RazorRecon — API Client
 * Handles REST + SSE communication with the FastAPI backend.
 */

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ── Helper ──────────────────────────────────────────────────────────────────

async function apiFetch(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`API ${res.status}: ${errorText}`);
  }
  return res.json();
}

// ── Reconciliation ────────────────────────────────────────────────────────────

/** POST /api/recon/run — triggers a new reconciliation run (scope: 'all' | 'imported') */
export async function triggerRecon(scope = 'all') {
  return apiFetch(`/api/recon/run?scope=${scope}`, { method: 'POST' });
}

/**
 * GET /api/recon/stream/{run_id} — SSE event stream.
 * @param {string} runId
 * @param {function} onEvent — called with { event, data } for each SSE message
 * @returns {EventSource} — call .close() to unsubscribe
 */
export function subscribeToRecon(runId, onEvent) {
  const es = new EventSource(`${BASE_URL}/api/recon/stream/${runId}`);

  es.addEventListener('progress', (e) => {
    try { onEvent({ event: 'progress', data: JSON.parse(e.data) }); } catch { /* ignore */ }
  });
  es.addEventListener('complete', (e) => {
    try {
      onEvent({ event: 'complete', data: JSON.parse(e.data) });
      es.close();
    } catch { /* ignore */ }
  });
  // Named error handler — fires at most once per EventSource lifetime.
  // Both the server-sent 'error' event and the browser-level onerror can fire;
  // the guard prevents a double RECON_ERROR dispatch and a second es.close() call.
  let errorFired = false;
  const handleSseError = (data) => {
    if (errorFired) return;
    errorFired = true;
    onEvent({ event: 'error', data });
    es.close();
  };

  es.addEventListener('error', (e) => {
    try {
      const data = e.data ? JSON.parse(e.data) : { message: 'SSE error' };
      handleSseError(data);
    } catch { handleSseError({ message: 'SSE error' }); }
  });
  es.addEventListener('keepalive', () => { /* noop */ });

  es.onerror = () => {
    handleSseError({ message: 'Connection to backend lost' });
  };

  return es;
}

/** GET /api/recon/results/{run_id} — full results (all 100 records) */
export async function fetchResults(runId) {
  return apiFetch(`/api/recon/results/${runId}`);
}

/** GET /api/recon/stats/{run_id} — aggregated stats */
export async function fetchStats(runId) {
  return apiFetch(`/api/recon/stats/${runId}`);
}

// ── Cash Flow ─────────────────────────────────────────────────────────────────

/** GET /api/cashflow/{run_id} — 7-day projection */
export async function fetchCashFlow(runId) {
  return apiFetch(`/api/cashflow/${runId}`);
}

/**
 * POST /api/cashflow/whatif — simulate resolving a break
 * @param {string} runId
 * @param {string} breakOrderId
 */
export async function resolveBreak(runId, breakOrderId) {
  return apiFetch('/api/cashflow/whatif', {
    method: 'POST',
    body: JSON.stringify({ run_id: runId, break_order_id: breakOrderId }),
  });
}

// ── Audit Log ─────────────────────────────────────────────────────────────────

/** GET /api/audit/{run_id} — full audit log */
export async function fetchAuditLog(runId) {
  return apiFetch(`/api/audit/${runId}`);
}

/** Trigger audit JSON download */
export function exportAuditLog(runId) {
  window.open(`${BASE_URL}/api/audit/${runId}/export`, '_blank');
}

// ── Health ────────────────────────────────────────────────────────────────────

export async function checkHealth() {
  return apiFetch('/api/health');
}

// ── Ingestion / Batch Importer ────────────────────────────────────────────────

/**
 * POST /api/recon/upload — upload CSV or XLSX report file
 * @param {File} file
 * @param {'razorpay_settlement' | 'erp_ledger'} source
 */
export async function uploadCSVFile(file, source) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('source', source);

  const res = await fetch(`${BASE_URL}/api/recon/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`Upload failed (${res.status}): ${errorText}`);
  }
  return res.json();
}

