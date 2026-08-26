import { useState, useEffect } from 'react';
import { ClipboardList, Download, Filter, X } from 'lucide-react';
import { useReconciliation } from '../context/ReconciliationContext';
import { exportAuditLog } from '../api/client';
import './AuditLogPanel.css';

const PASS_LABELS = { 1: 'Exact Match', 2: 'Rule-Based', 3: 'Fuzzy', 4: 'AI Diagnostics' };
const PASS_COLORS = { 1: 'pass-1', 2: 'pass-2', 3: 'pass-3', 4: 'pass-4' };

export default function AuditLogPanel({ isOpen, onClose }) {
  const { state, loadAuditLog } = useReconciliation();
  const { results, runId, auditLog } = state;

  const [passFilter, setPassFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    if (isOpen && runId && !auditLog) {
      loadAuditLog();
    }
  }, [isOpen, runId, auditLog, loadAuditLog]);

  if (!isOpen) return null;

  const entries = auditLog?.entries || results.map((r, i) => ({ ...r, id: r.id || i }));

  const filtered = entries.filter(e => {
    if (passFilter !== 'all' && e.pass_number !== parseInt(passFilter)) return false;
    if (statusFilter !== 'all' && e.status !== statusFilter) return false;
    return true;
  });

  return (
    <div className="audit-overlay animate-fadeIn" onClick={onClose}>
      <aside
        className="audit-sidepanel animate-slideLeft"
        onClick={e => e.stopPropagation()}
        id="audit-log-panel"
        role="dialog"
        aria-label="Audit Log Side Panel"
      >
        {/* Side Panel Header */}
        <div className="audit-panel-header">
          <div className="audit-panel-title-group">
            <ClipboardList size={18} className="text-blue" />
            <div>
              <h3>Audit Trail &amp; Execution Log</h3>
              <span className="audit-count">
                {auditLog ? auditLog.total_entries : results.length} total entries
              </span>
            </div>
          </div>
          <div className="audit-panel-actions">
            {runId && (
              <button
                id="export-audit-btn"
                className="btn btn-secondary btn-sm"
                onClick={() => exportAuditLog(runId)}
                title="Export as JSON"
              >
                <Download size={12} /> Export
              </button>
            )}
            <button className="audit-close-btn" onClick={onClose} aria-label="Close Audit Log">
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Side Panel Body */}
        <div className="audit-panel-body">
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
              <option value="1">Pass 1 — Exact Match</option>
              <option value="2">Pass 2 — Rule-Based</option>
              <option value="3">Pass 3 — Fuzzy</option>
              <option value="4">Pass 4 — AI Diagnostics</option>
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
          </div>

          <div className="audit-results-count">{filtered.length} entries shown</div>

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
      </aside>
    </div>
  );
}
