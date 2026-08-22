import { useState, useEffect } from 'react';
import { ClipboardList, ChevronDown, ChevronUp, Download, Filter } from 'lucide-react';
import { useReconciliation } from '../context/ReconciliationContext';
import { exportAuditLog } from '../api/client';
import './AuditLogPanel.css';

const PASS_LABELS = { 1: 'Exact Match', 2: 'Rule-Based', 3: 'Fuzzy', 4: 'AI Diagnostics' };
const PASS_COLORS = { 1: 'pass-1', 2: 'pass-2', 3: 'pass-3', 4: 'pass-4' };

export default function AuditLogPanel() {
  const { state, loadAuditLog } = useReconciliation();
  const { results, runId, status, auditLog } = state;

  const [open, setOpen] = useState(false);
  const [passFilter, setPassFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    if (open && runId && !auditLog) {
      loadAuditLog();
    }
  }, [open, runId, auditLog, loadAuditLog]);

  const entries = auditLog?.entries || results.map((r, i) => ({ ...r, id: r.id || i }));

  const filtered = entries.filter(e => {
    if (passFilter !== 'all' && e.pass_number !== parseInt(passFilter)) return false;
    if (statusFilter !== 'all' && e.status !== statusFilter) return false;
    return true;
  });

  if (status === 'idle') return null;

  return (
    <div className="audit-panel" id="audit-log-panel">
      <button
        id="audit-toggle"
        className="audit-toggle"
        onClick={() => setOpen(o => !o)}
        aria-expanded={open}
      >
        <div className="audit-toggle-left">
          <ClipboardList size={15} />
          <span>Audit Log</span>
          <span className="audit-count">{results.length} entries</span>
        </div>
        <div className="audit-toggle-right">
          {runId && (
            <button
              id="export-audit-btn"
              className="btn btn-secondary btn-sm"
              onClick={e => { e.stopPropagation(); exportAuditLog(runId); }}
              title="Export as JSON"
            >
              <Download size={12} /> Export JSON
            </button>
          )}
          {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </div>
      </button>

      {open && (
        <div className="audit-content">
          {/* Filters */}
          <div className="audit-filters">
            <Filter size={12} className="text-tertiary" />
            <select
              id="audit-pass-filter"
              className="input audit-select"
              value={passFilter}
              onChange={e => setPassFilter(e.target.value)}
            >
              <option value="all">All Passes</option>
              <option value="1">Pass 1 — Exact</option>
              <option value="2">Pass 2 — Rule-Based</option>
              <option value="3">Pass 3 — Fuzzy</option>
              <option value="4">Pass 4 — AI</option>
            </select>
            <select
              id="audit-status-filter"
              className="input audit-select"
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value)}
            >
              <option value="all">All Statuses</option>
              <option value="matched">Matched</option>
              <option value="break">Break</option>
            </select>
            <span className="audit-filter-count">{filtered.length} entries</span>
          </div>

          {/* Timeline */}
          <div className="audit-timeline">
            {filtered.map(entry => (
              <div
                key={entry.id || entry.order_id}
                className={`audit-entry ${entry.status === 'break' ? 'audit-entry--break' : ''}`}
                id={`audit-${entry.order_id}`}
              >
                <div className="audit-entry-pass">
                  <span className={`pass-pill ${PASS_COLORS[entry.pass_number]}`}>
                    {entry.pass_number}
                  </span>
                  <div className="audit-entry-line" />
                </div>
                <div className="audit-entry-body">
                  <div className="audit-entry-header">
                    <span className="mono audit-order-id">{entry.order_id}</span>
                    <span className={`badge ${entry.status === 'matched' ? 'badge-matched' : 'badge-break'}`}>
                      {entry.status}
                    </span>
                    {entry.confidence != null && (
                      <span className="audit-conf">{(entry.confidence * 100).toFixed(0)}%</span>
                    )}
                  </div>
                  <div className="audit-entry-meta">
                    <span className="text-tertiary text-xs">{PASS_LABELS[entry.pass_number]}</span>
                    {entry.flags?.map(f => (
                      <span key={f} className="flag-tag">{f}</span>
                    ))}
                    {entry.severity && entry.status === 'break' && (
                      <span className={`severity-dot ${entry.severity}`} />
                    )}
                  </div>
                </div>
              </div>
            ))}
            {filtered.length === 0 && (
              <p className="audit-empty">No entries match the current filters.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
