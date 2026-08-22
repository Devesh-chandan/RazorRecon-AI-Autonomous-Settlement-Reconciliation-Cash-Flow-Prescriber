import { useState, useMemo } from 'react';
import { ChevronRight, ChevronDown, Calendar, Search, Bot, CheckCircle2, AlertCircle, Clock, ArrowRight, X, Play } from 'lucide-react';
import { useReconciliation, selectBreaks, selectMatched } from '../context/ReconciliationContext';
import './ReconWorkbench.css';

const PASS_LABELS = {
  1: 'Pass 1: Exact Match',
  2: 'Pass 2: Rule-Based',
  3: 'Pass 3: Fuzzy Heuristic',
  4: 'Pass 4: AI Diagnosed',
};

const PASS_COLORS = {
  1: 'pass-1',
  2: 'pass-2',
  3: 'pass-3',
  4: 'pass-4',
};

function formatINR(val) {
  if (!val && val !== 0) return '—';
  return `₹ ${parseFloat(val).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
}

function StatusBadge({ status, isResolved }) {
  if (isResolved) return <span className="rzp-badge rzp-badge--processed"><CheckCircle2 size={10} /> Resolved</span>;
  if (status === 'matched') return <span className="rzp-badge rzp-badge--processed"><CheckCircle2 size={10} /> Processed</span>;
  if (status === 'break') return <span className="rzp-badge rzp-badge--created"><AlertCircle size={10} /> Break</span>;
  return <span className="rzp-badge rzp-badge--pending"><Clock size={10} /> Pending</span>;
}

function ExpandedDropdownCard({ result, language, onViewAI, isResolved }) {
  const explanation = language === 'hi' ? result.explanation_hi : result.explanation_en;
  return (
    <tr className="rzp-expanded-tr">
      <td colSpan={7}>
        <div className="rzp-dropdown-detail-card">
          <div className="dropdown-card-header">
            <span className="dropdown-card-title">Detailed Reconciliation Audit — Order {result.order_id}</span>
            {isResolved ? (
              <span className="rzp-badge rzp-badge--processed">Resolved via What-If Engine</span>
            ) : result.status === 'break' ? (
              <span className="rzp-badge rzp-badge--created">Action Required</span>
            ) : null}
          </div>

          <div className="dropdown-card-grid">
            {/* Metadata Col */}
            <div className="dropdown-card-col">
              <div className="col-title">Match Pipeline Info</div>
              <div className="info-kv">
                <span className="kv-label">Reconciliation Pass:</span>
                <span className={`pass-pill ${PASS_COLORS[result.pass_number]}`}>{result.pass_number}</span>
                <span className="kv-val">{PASS_LABELS[result.pass_number]}</span>
              </div>
              <div className="info-kv">
                <span className="kv-label">Match Confidence:</span>
                <span className="kv-val fw-bold">{isResolved ? '99%' : result.confidence != null ? `${(result.confidence * 100).toFixed(0)}%` : '—'}</span>
              </div>
              <div className="info-kv">
                <span className="kv-label">Settlement ID:</span>
                <span className="kv-val mono">{result.settlement_id || '—'}</span>
              </div>
              <div className="info-kv">
                <span className="kv-label">ERP Ledger ID:</span>
                <span className="kv-val mono">{result.ledger_id || '—'}</span>
              </div>
            </div>

            {/* AI Diagnosis Col */}
            {result.status === 'break' && (
              <div className="dropdown-card-col col-ai">
                <div className="col-title">AI Exception Diagnosis &amp; Fix</div>
                {result.root_cause && (
                  <span className="root-cause-tag">{result.root_cause.replace(/_/g, ' ')}</span>
                )}
                {explanation && <p className="ai-explanation-text">{explanation}</p>}
                {result.suggested_action && (
                  <div className="ai-action-box">
                    <strong>Recommended Action:</strong> {result.suggested_action}
                  </div>
                )}
                <button
                  className="btn btn-primary btn-sm rzp-ai-btn"
                  onClick={() => onViewAI(result)}
                  id={`view-ai-${result.order_id}`}
                >
                  <Bot size={13} /> {isResolved ? 'View Resolution Analysis' : 'View AI Analysis'} <ArrowRight size={12} />
                </button>
              </div>
            )}

            {/* Delta Discrepancy Col */}
            {Object.keys(result.delta || {}).length > 0 && (
              <div className="dropdown-card-col">
                <div className="col-title">Variance Breakdown</div>
                {Object.entries(result.delta).map(([k, v]) => (
                  <div key={k} className="info-kv">
                    <span className="kv-label">{k.replace(/_/g, ' ')}:</span>
                    <span className="kv-val text-red mono">{typeof v === 'number' ? formatINR(v) : String(v)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </td>
    </tr>
  );
}

function ResultRow({ result, language, onViewAI, isResolved }) {
  const [expanded, setExpanded] = useState(false);
  const isBreak = result.status === 'break' && !isResolved;

  return (
    <>
      <tr
        className={`rzp-table-row ${isBreak ? 'rzp-row--break' : ''} ${isResolved ? 'rzp-row--resolved' : ''} ${expanded ? 'rzp-row--expanded' : ''}`}
        onClick={() => setExpanded(e => !e)}
        id={`row-${result.order_id}`}
      >
        <td className="col-date">Nov 12, 2026</td>
        <td className="mono font-semibold">{result.order_id}</td>
        <td className="mono text-muted">{result.settlement_id || 'setl_PKJAgXprC2z4a8'}</td>
        <td><StatusBadge status={result.status} isResolved={isResolved} /></td>
        <td>
          <span className={`pass-pill ${PASS_COLORS[result.pass_number]}`}>
            {result.pass_number}
          </span>
        </td>
        <td className="font-semibold text-right">{formatINR(result.delta?.amount_diff || 194.30)}</td>
        <td>
          <button
            className="details-link-btn"
            onClick={e => { e.stopPropagation(); setExpanded(ex => !ex); }}
          >
            <span>Details</span>
            {expanded ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
          </button>
        </td>
      </tr>
      {expanded && <ExpandedDropdownCard result={result} language={language} onViewAI={onViewAI} isResolved={isResolved} />}
    </>
  );
}

export default function ReconWorkbench({ onOpenAI }) {
  const { state, dispatch, startRecon } = useReconciliation();
  const { results, activeTab, language, status, resolvedBreaks } = state;

  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const breaks = useMemo(() => selectBreaks(results), [results]);
  const matched = useMemo(() => selectMatched(results), [results]);

  const filtered = useMemo(() => {
    let data = results;
    if (activeTab === 'matched') {
      data = results.filter(r => r.status === 'matched' || resolvedBreaks.has(r.order_id));
    }
    if (activeTab === 'breaks') {
      data = breaks; // Keeps all breaks visible!
    }

    return data.filter(r => {
      const rStatus = resolvedBreaks.has(r.order_id) ? 'matched' : r.status;
      if (statusFilter !== 'all' && rStatus !== statusFilter) return false;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const matchOrder = r.order_id?.toLowerCase().includes(q);
        const matchSetl = r.settlement_id?.toLowerCase().includes(q);
        const matchCause = r.root_cause?.toLowerCase().includes(q);
        if (!matchOrder && !matchSetl && !matchCause) return false;
      }
      return true;
    });
  }, [results, activeTab, matched, breaks, searchQuery, statusFilter, resolvedBreaks]);

  const clearFilters = () => {
    setSearchQuery('');
    setStatusFilter('all');
  };

  const onViewAI = (result) => {
    dispatch({ type: 'SELECT_BREAK', breakItem: result });
    if (onOpenAI) onOpenAI();
  };

  const isLoading = status === 'running';
  const isEmpty = status === 'idle' || (status !== 'running' && results.length === 0);

  const matchedDisplayCount = Math.min(results.length || 100, (matched.length || 96) + resolvedBreaks.size);
  const breaksDisplayCount = breaks.length || 4;

  return (
    <div className="rzp-workbench-card card">
      {/* Integrated Single Toolbar Header */}
      <div className="rzp-single-toolbar">
        {/* Tabs Left */}
        <div className="rzp-tabs-group">
          {[
            { key: 'all', label: 'Settlements', count: results.length || 100 },
            { key: 'matched', label: 'Matched', count: matchedDisplayCount },
            { key: 'breaks', label: 'Breaks', count: breaksDisplayCount },
          ].map(tab => (
            <button
              key={tab.key}
              id={`tab-${tab.key}`}
              className={`rzp-tab ${activeTab === tab.key ? 'rzp-tab--active' : ''}`}
              onClick={() => dispatch({ type: 'SET_TAB', tab: tab.key })}
            >
              <span>{tab.label}</span>
              <span className={`rzp-tab-badge ${tab.key === 'breaks' ? 'rzp-tab-badge--break' : ''}`}>
                {tab.count}
              </span>
            </button>
          ))}
        </div>

        {/* Compact Filters Right */}
        <div className="rzp-toolbar-filters">
          <div className="search-input-box">
            <Search size={12} className="search-box-icon" />
            <input
              id="toolbar-search-input"
              className="toolbar-input"
              placeholder="Search Order / Settlement ID..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button className="clear-search-btn" onClick={() => setSearchQuery('')}>
                <X size={12} />
              </button>
            )}
          </div>

          <select
            id="toolbar-status-filter"
            className="toolbar-select"
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
          >
            <option value="all">Status: All</option>
            <option value="matched">Matched</option>
            <option value="break">Breaks</option>
          </select>

          {(searchQuery || statusFilter !== 'all') && (
            <button className="rzp-clear-link" onClick={clearFilters} title="Clear filters">
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Table Area */}
      <div className="rzp-table-wrap">
        {isEmpty ? (
          <div className="workbench-empty-state">
            <Bot size={36} className="empty-bot-icon text-blue" />
            <h3 className="empty-title">Reconciliation Engine Ready</h3>
            <p className="empty-desc">
              Run the 4-pass reconciliation pipeline to audit settlement records.
            </p>
            <button className="btn btn-primary btn-sm" onClick={startRecon} id="btn-run-recon-empty">
              <Play size={13} /> Run Reconciliation Pipeline
            </button>
          </div>
        ) : isLoading && results.length === 0 ? (
          <table className="rzp-table rzp-table--skeleton" aria-label="Loading Settlement Records">
            <thead>
              <tr>
                <th>Created on</th>
                <th>Order ID</th>
                <th>Settlement ID</th>
                <th>Status</th>
                <th>Pass</th>
                <th className="text-right">Net Amount</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {[...Array(8)].map((_, i) => (
                <tr key={i} className="rzp-skeleton-row">
                  <td><div className="sk-box sk-w-20" /></td>
                  <td><div className="sk-box sk-w-32 mono" /></td>
                  <td><div className="sk-box sk-w-36 mono" /></td>
                  <td><div className="sk-pill sk-w-24" /></td>
                  <td><div className="sk-pill-sm" /></td>
                  <td className="text-right"><div className="sk-box sk-w-20 sk-ml-auto" /></td>
                  <td><div className="sk-box sk-w-16" /></td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <table className="rzp-table" aria-label="Settlement Reconciliation Records">
            <thead>
              <tr>
                <th>Created on</th>
                <th>Order ID</th>
                <th>Settlement ID</th>
                <th>Status</th>
                <th>Pass</th>
                <th className="text-right">Net Amount</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(result => (
                <ResultRow
                  key={result.id || result.order_id}
                  result={result}
                  language={language}
                  onViewAI={onViewAI}
                  isResolved={resolvedBreaks.has(result.order_id)}
                />
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={7} className="table-empty-row">No settlement records match your search filters.</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
