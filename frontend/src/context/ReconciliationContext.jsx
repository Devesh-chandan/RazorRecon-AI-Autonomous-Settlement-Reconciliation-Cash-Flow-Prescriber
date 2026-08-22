import { createContext, useContext, useReducer, useCallback } from 'react';
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
};

// ── Reducer ───────────────────────────────────────────────────────────────────

function reducer(state, action) {
  switch (action.type) {
    case 'RUN_RECON':
      return { ...state, status: 'running', runId: action.runId, progress: {}, results: [], stats: {}, error: null, whatIfScenario: null, resolvedBreaks: new Set() };

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

    case 'RESOLVE_BREAK':
      const newResolved = new Set(state.resolvedBreaks);
      newResolved.add(action.orderId);
      return { ...state, resolvedBreaks: newResolved };

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

  // ── Start Reconciliation ──────────────────────────────────────────────────
  const startRecon = useCallback(async () => {
    try {
      const { run_id } = await triggerRecon();
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
  return results.filter(r => r.status === 'break');
}

export function selectMatched(results) {
  return results.filter(r => r.status === 'matched');
}
