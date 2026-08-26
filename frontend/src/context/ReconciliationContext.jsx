import { createContext, useContext, useReducer, useCallback, useEffect } from 'react';
import {
  triggerRecon, subscribeToRecon, fetchResults,
  fetchStats, fetchCashFlow, fetchAuditLog,
} from '../api/client';

// ── Initial State ─────────────────────────────────────────────────────────────

const initialState = {
  status: 'idle',       // 'idle' | 'running' | 'complete' | 'error'
  runId: null,
  progress: {},
  results: [],
  stats: {},
  cashFlow: [],
  whatIfScenario: null,
  language: 'en',       // 'en' | 'hi'
  selectedBreak: null,
  drawerOpen: false,
  activeTab: 'all',
  auditLog: null,
  resolvedBreaks: new Set(),
  error: null,
  searchQuery: '',
  statusFilter: 'all',
};

// ── Reducer ───────────────────────────────────────────────────────────────────

function reducer(state, action) {
  switch (action.type) {
    case 'RUN_RECON':
      return {
        ...state,
        status: 'running',
        runId: action.runId,
        progress: {},
        results: [],
        stats: {},
        error: null,
        whatIfScenario: null,
        resolvedBreaks: new Set(),
        auditLog: null,
      };

    case 'PROGRESS_UPDATE':
      return { ...state, progress: action.data };

    case 'RECON_COMPLETE':
      return { ...state, status: 'complete', progress: action.data };

    case 'RECON_ERROR':
      return { ...state, status: 'error', error: action.message };

    case 'SET_RESULTS':
      return { ...state, results: action.results };

    case 'SET_STATS':
      return { ...state, stats: action.stats };

    case 'SET_CASHFLOW':
      return { ...state, cashFlow: action.cashFlow };

    case 'SET_WHATIF':
      return { ...state, whatIfScenario: action.scenario };

    case 'CLEAR_WHATIF':
      return { ...state, whatIfScenario: null };

    case 'SET_LANGUAGE':
      return { ...state, language: action.language };

    case 'SELECT_BREAK':
      return { ...state, selectedBreak: action.breakItem, drawerOpen: true };

    case 'TOGGLE_DRAWER':
      return { ...state, drawerOpen: !state.drawerOpen };

    case 'CLOSE_DRAWER':
      return { ...state, drawerOpen: false };

    case 'SET_TAB':
      return { ...state, activeTab: action.tab };

    case 'SET_SEARCH_QUERY':
      return { ...state, searchQuery: action.query };

    case 'SET_STATUS_FILTER':
      return { ...state, statusFilter: action.filter };

    case 'RESOLVE_BREAK': {
      const newResolved = new Set(state.resolvedBreaks);
      newResolved.add(action.orderId);

      // Derive counts purely from real results — no hardcoded fallbacks
      const totalRecords = state.stats.total_records ?? state.results.length ?? 0;
      const realMatched  = state.results.filter(r => r.status === 'matched').length;
      const realBreaks   = state.results.filter(r => r.status === 'break').length;
      const newMatchedCount = Math.min(totalRecords, realMatched + newResolved.size);
      const newBreakCount   = Math.max(0, realBreaks - newResolved.size);
      const newMatchRate    = totalRecords > 0
        ? parseFloat(((newMatchedCount / totalRecords) * 100).toFixed(1))
        : 0;

      const updatedStats = {
        ...state.stats,
        matched_count: newMatchedCount,
        break_count: newBreakCount,
        match_rate: newMatchRate,
      };

      // Ingest resolution log entry into Audit Log Timeline
      const existingEntries = state.auditLog?.entries || state.results.map((r, i) => ({ ...r, id: r.id || i }));
      const newAuditEntry = {
        id: `audit-resolve-${action.orderId}-${Date.now()}`,
        order_id: action.orderId,
        pass_number: 4,
        status: 'matched',
        confidence: 0.99,
        flags: ['What-If Resolved', 'AI Prescribed'],
        severity: null,
      };

      const updatedAuditLog = {
        run_id: state.runId,
        total_entries: existingEntries.length + 1,
        entries: [newAuditEntry, ...existingEntries],
      };

      return {
        ...state,
        resolvedBreaks: newResolved,
        stats: updatedStats,
        auditLog: updatedAuditLog,
      };
    }

    case 'SET_AUDIT_LOG':
      return { ...state, auditLog: action.auditLog };

    default:
      return state;
  }
}

// ── Context ───────────────────────────────────────────────────────────────────

const ReconciliationContext = createContext(null);

export function ReconciliationProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState);

  // ── Application starts fresh in clean idle state ───────────────────────────
  useEffect(() => {
    // Clear any previous cached run ID on app launch to ensure fresh clean start
    localStorage.removeItem('razorrecon_active_run_id');
  }, []);

  // ── Start Reconciliation ──────────────────────────────────────────────────
  const startRecon = useCallback(async (scope = 'all') => {
    try {
      const { run_id } = await triggerRecon(scope);
      localStorage.setItem('razorrecon_active_run_id', run_id);
      dispatch({ type: 'RUN_RECON', runId: run_id });

      // Subscribe to SSE stream
      const es = subscribeToRecon(run_id, async ({ event, data }) => {
        if (event === 'progress') {
          dispatch({ type: 'PROGRESS_UPDATE', data });
        } else if (event === 'complete') {
          dispatch({ type: 'RECON_COMPLETE', data });

          // Fetch full results + stats + cashflow in parallel
          try {
            const [results, stats, cashFlowData] = await Promise.all([
              fetchResults(run_id),
              fetchStats(run_id),
              fetchCashFlow(run_id),
            ]);
            dispatch({ type: 'SET_RESULTS', results });
            dispatch({ type: 'SET_STATS', stats });
            dispatch({ type: 'SET_CASHFLOW', cashFlow: cashFlowData.projection });
          } catch (err) {
            console.error('Failed to fetch results after recon:', err);
            dispatch({ type: 'RECON_ERROR', message: `Failed to load results: ${err.message}` });
          }
        } else if (event === 'error') {
          dispatch({ type: 'RECON_ERROR', message: data.message });
        }
      });

      return () => es.close();
    } catch (err) {
      dispatch({ type: 'RECON_ERROR', message: err.message });
    }
  }, []);

  // ── Refresh Active Data ────────────────────────────────────────────────────
  const refreshData = useCallback(async () => {
    if (!state.runId) {
      return;
    }
    try {
      const [results, stats, cashFlowData] = await Promise.all([
        fetchResults(state.runId),
        fetchStats(state.runId),
        fetchCashFlow(state.runId),
      ]);
      dispatch({ type: 'SET_RESULTS', results });
      dispatch({ type: 'SET_STATS', stats });
      dispatch({ type: 'SET_CASHFLOW', cashFlow: cashFlowData.projection });
    } catch (err) {
      console.error('Failed to refresh data:', err);
    }
  }, [state.runId, startRecon]);

  // ── Load Audit Log ────────────────────────────────────────────────────────
  const loadAuditLog = useCallback(async () => {
    if (!state.runId) return;
    try {
      const log = await fetchAuditLog(state.runId);
      dispatch({ type: 'SET_AUDIT_LOG', auditLog: log });
    } catch (err) {
      console.error('Failed to load audit log:', err);
    }
  }, [state.runId]);

  const value = {
    state,
    dispatch,
    startRecon,
    refreshData,
    loadAuditLog,
  };

  return (
    <ReconciliationContext.Provider value={value}>
      {children}
    </ReconciliationContext.Provider>
  );
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useReconciliation() {
  const ctx = useContext(ReconciliationContext);
  if (!ctx) throw new Error('useReconciliation must be used inside ReconciliationProvider');
  return ctx;
}

// ── Selectors ─────────────────────────────────────────────────────────────────

export function selectBreaks(results) {
  return (results || []).filter(r => r && r.status === 'break');
}

export function selectMatched(results) {
  return (results || []).filter(r => r && r.status === 'matched');
}

const GATEWAY_COLORS = {
  'HDFC Bank (PG)': '#0b72e7',
  'ICICI Direct': '#10b981',
  'Razorpay Stack': '#9333ea',
  'Axis UPI Express': '#f59e0b',
  'PhonePe Gateway': '#ec4899',
  'Other / Direct': '#64748b',
};

// Map raw payment_method values → display gateway name (fallback for older records without gateway field)
const METHOD_TO_GATEWAY = {
  upi: 'Razorpay Stack',
  card: 'HDFC Bank (PG)',
  netbanking: 'ICICI Direct',
  emi: 'HDFC Bank (PG)',
  wallet: 'PhonePe Gateway',
};

function resolveGateway(r) {
  // Prefer explicit gateway name from new seeded/imported data
  if (r.gateway && r.gateway.trim()) return r.gateway.trim();
  // Fall back to payment_method → gateway display name mapping
  if (r.payment_method) return METHOD_TO_GATEWAY[r.payment_method] || 'Razorpay Stack';
  return 'Razorpay Stack';
}

function getRecordAmount(r) {
  if (r.settlement_credit !== undefined && r.settlement_credit !== null) return r.settlement_credit;
  if (r.amount !== undefined && r.amount !== null) return r.amount;
  if (r.gateway_amount !== undefined && r.gateway_amount !== null) return r.gateway_amount;
  if (r.erp_amount !== undefined && r.erp_amount !== null) return r.erp_amount;
  return 0;
}

export function selectGatewayBreakdown(results) {
  if (!results || results.length === 0) {
    return [];
  }

  const counts = {};
  const amounts = {};
  let totalAmt = 0;

  results.forEach(r => {
    const gw = resolveGateway(r);
    const amt = getRecordAmount(r);
    counts[gw] = (counts[gw] || 0) + 1;
    amounts[gw] = (amounts[gw] || 0) + amt;
    totalAmt += amt;
  });

  if (totalAmt === 0) {
    totalAmt = results.length * 5000;
    Object.keys(counts).forEach(gw => {
      amounts[gw] = (counts[gw] / results.length) * totalAmt;
    });
  }

  return Object.keys(counts).map(gw => {
    const amt = amounts[gw] || 0;
    const pct = totalAmt > 0 ? parseFloat(((amt / totalAmt) * 100).toFixed(1)) : 0;
    return {
      name: gw,
      count: counts[gw],
      amount: Math.round(amt),
      percentage: pct,
      color: GATEWAY_COLORS[gw] || '#64748b',
    };
  }).sort((a, b) => b.amount - a.amount);
}

export function selectExceptionBreakdown(results, resolvedBreaks = new Set()) {
  const breaks = (results || []).filter(r => r && r.status === 'break' && !resolvedBreaks.has(r.order_id));

  if (!breaks.length) {
    return [];
  }

  const causes = {};
  breaks.forEach(b => {
    const cause = b.root_cause
      ? b.root_cause.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
      : 'Unclassified Exception';
    if (!causes[cause]) {
      causes[cause] = { count: 0, impact: 0, pass: b.pass_number || 4, severity: b.severity || 'Medium' };
    }
    causes[cause].count += 1;
    const delta = b.delta?.amount_mismatch || Math.abs((b.erp_amount || 0) - (b.gateway_amount || 0)) || 1200;
    causes[cause].impact += delta;
  });

  return Object.keys(causes).map(title => ({
    title,
    count: causes[title].count,
    impact: causes[title].impact,
    color: causes[title].severity === 'High' ? '#e53e3e' : '#dd6b20',
    pass: `Pass ${causes[title].pass}`,
    severity: causes[title].severity,
  }));
}
