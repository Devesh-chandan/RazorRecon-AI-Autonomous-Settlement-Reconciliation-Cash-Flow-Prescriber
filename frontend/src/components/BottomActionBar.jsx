import { useMemo } from 'react';
import { Bot, ClipboardList, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';
import { useReconciliation, selectBreaks } from '../context/ReconciliationContext';
import './BottomActionBar.css';

export default function BottomActionBar({ activeOverlay, setActiveOverlay }) {
  const { state } = useReconciliation();
  const { results, resolvedBreaks, status, runId, auditLog } = state;

  const breaks = useMemo(() => selectBreaks(results), [results]);
  const unresolvedBreaksCount = Math.max(0, breaks.length - resolvedBreaks.size);
  const auditEntriesCount = auditLog?.entries?.length || results.length;

  const toggleAI = () => {
    setActiveOverlay(activeOverlay === 'ai' ? null : 'ai');
  };

  const toggleAudit = () => {
    setActiveOverlay(activeOverlay === 'audit' ? null : 'audit');
  };

  return (
    <div className="bottom-action-bar" id="bottom-action-bar">
      <div className="bottom-bar-left">
        {/* Status Indicator */}
        <div className="bottom-status-pill">
          {status === 'running' ? (
            <>
              <RefreshCw size={12} className="animate-spin text-blue" />
              <span>Processing Multi-Pass Pipeline...</span>
            </>
          ) : status === 'complete' ? (
            <>
              <CheckCircle2 size={12} className="text-green" />
              <span>Reconciliation Synchronized</span>
            </>
          ) : (
            <>
              <span className="status-dot-idle" />
              <span>System Ready</span>
            </>
          )}
        </div>
      </div>

      <div className="bottom-bar-right">
        {/* AI Diagnostics Drawer Toggle */}
        <button
          id="btn-bottom-ai"
          className={`bottom-pill-btn ${activeOverlay === 'ai' ? 'bottom-pill-btn--active' : ''} ${unresolvedBreaksCount > 0 ? 'bottom-pill-btn--alert' : ''}`}
          onClick={toggleAI}
          aria-label="Toggle AI Exception Analysis Drawer"
        >
          <Bot size={14} className="pill-icon" />
          <span>AI Exception Analysis</span>
          {unresolvedBreaksCount > 0 ? (
            <span className="pill-badge pill-badge--error">{unresolvedBreaksCount} unresolved</span>
          ) : breaks.length > 0 ? (
            <span className="pill-badge pill-badge--success">{resolvedBreaks.size} resolved</span>
          ) : null}
        </button>

        {/* Audit Log Drawer Toggle */}
        <button
          id="btn-bottom-audit"
          className={`bottom-pill-btn ${activeOverlay === 'audit' ? 'bottom-pill-btn--active' : ''}`}
          onClick={toggleAudit}
          aria-label="Toggle Audit Log Panel"
        >
          <ClipboardList size={14} className="pill-icon" />
          <span>Audit Log</span>
          {auditEntriesCount > 0 && (
            <span className="pill-badge">{auditEntriesCount} entries</span>
          )}
        </button>
      </div>
    </div>
  );
}
