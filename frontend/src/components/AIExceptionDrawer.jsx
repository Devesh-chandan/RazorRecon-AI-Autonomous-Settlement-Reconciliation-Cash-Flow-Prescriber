import { useMemo, useState } from 'react';
import { Bot, X, CheckCircle, ArrowUpRight, ChevronUp, ChevronDown, AlertTriangle } from 'lucide-react';
import { useReconciliation, selectBreaks } from '../context/ReconciliationContext';
import { resolveBreak } from '../api/client';
import './AIExceptionDrawer.css';

const SEVERITY_CONFIG = {
  critical: { label: 'Critical', className: 'severity-critical' },
  high:     { label: 'High',     className: 'severity-high' },
  medium:   { label: 'Medium',   className: 'severity-medium' },
  low:      { label: 'Low',      className: 'severity-low' },
};

const ROOT_CAUSE_LABELS = {
  mdr_variance:      'MDR Variance',
  timing_lag:        'Timing Lag',
  missing_erp_entry: 'Missing ERP Entry',
  data_entry_error:  'Data Entry Error',
  chargeback:        'Chargeback',
  partial_refund:    'Partial Refund',
  gst_rounding:      'GST Rounding',
  duplicate_entry:   'Duplicate Entry',
  unknown:           'Unknown',
};

function BreakCard({ result, language, onResolve, onEscalate, isResolved, runId }) {
  const [resolving, setResolving] = useState(false);
  const explanation = language === 'hi' ? result.explanation_hi : result.explanation_en;
  const sev = SEVERITY_CONFIG[result.severity] || SEVERITY_CONFIG.medium;

  const handleResolve = async () => {
    if (resolving || isResolved) return;
    setResolving(true);
    try {
      await onResolve(result.order_id);
    } finally {
      setResolving(false);
    }
  };

  return (
    <div className={`break-card ${isResolved ? 'break-card--resolved' : ''}`} id={`break-${result.order_id}`}>
      <div className="break-card-header">
        <div className="break-card-left">
          <span className={`severity-badge ${sev.className}`}>
            <span className="severity-dot" />
            {sev.label}
          </span>
          <span className="mono break-order-id">{result.order_id}</span>
        </div>
        {result.root_cause && (
          <span className="root-cause-chip">
            {ROOT_CAUSE_LABELS[result.root_cause] || result.root_cause}
          </span>
        )}
      </div>

      <div className="break-card-body">
        {explanation ? (
          <p className="break-explanation">{explanation}</p>
        ) : (
          <p className="break-explanation break-explanation--empty">Analysis pending...</p>
        )}

        {result.suggested_action && (
          <div className="break-action">
            <AlertTriangle size={12} />
            <span>{result.suggested_action}</span>
          </div>
        )}
      </div>

      <div className="break-card-footer">
        {isResolved ? (
          <span className="resolved-badge"><CheckCircle size={12} /> Resolved (What-If Applied)</span>
        ) : (
          <>
            <button
              id={`resolve-${result.order_id}`}
              className="btn btn-success btn-sm"
              onClick={handleResolve}
              disabled={resolving}
              aria-label={`Resolve break for ${result.order_id}`}
            >
              <CheckCircle size={12} />
              {resolving ? 'Resolving...' : 'Resolve ✓'}
            </button>
            <button
              id={`escalate-${result.order_id}`}
              className="btn btn-secondary btn-sm"
              onClick={() => onEscalate(result)}
              aria-label={`Escalate break for ${result.order_id}`}
            >
              <ArrowUpRight size={12} />
              Escalate ↗
            </button>
          </>
        )}
        {result.confidence != null && (
          <span className="confidence-badge">
            {(result.confidence * 100).toFixed(0)}% confident
          </span>
        )}
      </div>
    </div>
  );
}

export default function AIExceptionDrawer() {
  const { state, dispatch } = useReconciliation();
  const { results, drawerOpen, language, resolvedBreaks, runId } = state;

  const breaks = useMemo(() => selectBreaks(results), [results]);

  const toggleDrawer = () => dispatch({ type: 'TOGGLE_DRAWER' });

  const handleResolve = async (orderId) => {
    if (!runId) return;
    try {
      const scenario = await resolveBreak(runId, orderId);
      dispatch({ type: 'SET_WHATIF', scenario });
      dispatch({ type: 'RESOLVE_BREAK', orderId });
    } catch (err) {
      console.error('What-if resolve failed:', err);
    }
  };

  const handleEscalate = (result) => {
    // In production: open a ticket creation flow
    alert(`Escalating ${result.order_id} to finance team.\n\nRoot cause: ${result.root_cause}\n\nIn production, this would create a support ticket.`);
  };

  if (!breaks.length && results.length === 0) return null;

  return (
    <div className={`ai-drawer ${drawerOpen ? 'ai-drawer--open' : ''}`} id="ai-exception-drawer">
      {/* Drawer Handle */}
      <button
        id="drawer-toggle"
        className="drawer-handle"
        onClick={toggleDrawer}
        aria-expanded={drawerOpen}
        aria-label={`${drawerOpen ? 'Close' : 'Open'} AI Exception Drawer`}
      >
        <div className="drawer-handle-left">
          <Bot size={16} className="drawer-bot-icon" />
          <span className="drawer-title">AI Exception Analysis</span>
          {breaks.length > 0 && (
            <span className="drawer-badge">{breaks.length - resolvedBreaks.size} unresolved</span>
          )}
        </div>
        <div className="drawer-handle-right">
          {resolvedBreaks.size > 0 && (
            <span className="resolved-count">
              <CheckCircle size={12} /> {resolvedBreaks.size} resolved
            </span>
          )}
          {drawerOpen ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
        </div>
      </button>

      {/* Drawer Content */}
      {drawerOpen && (
        <div className="drawer-content" role="region" aria-label="AI Exception Cards">
          {breaks.length === 0 ? (
            <div className="drawer-empty">
              <CheckCircle size={32} className="drawer-empty-icon" />
              <p>All records matched successfully! No breaks to review.</p>
            </div>
          ) : (
            <div className="drawer-cards">
              {breaks.map(result => (
                <BreakCard
                  key={result.id || result.order_id}
                  result={result}
                  language={language}
                  onResolve={handleResolve}
                  onEscalate={handleEscalate}
                  isResolved={resolvedBreaks.has(result.order_id)}
                  runId={runId}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
