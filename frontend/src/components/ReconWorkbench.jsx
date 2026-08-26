import { useState, useMemo } from 'react';
import { ChevronRight, ChevronDown, Search, Bot, CheckCircle2, AlertCircle, Clock, ArrowRight, X, Play, MoreHorizontal } from 'lucide-react';
import { useReconciliation, selectBreaks, selectMatched } from '../context/ReconciliationContext';
import './ReconWorkbench.css';

const PASS_LABELS = {
  1: 'Pass 1: Exact Match',
  2: 'Pass 2: Rule-Based',
  3: 'Pass 3: Fuzzy Heuristic',
  4: 'Pass 4: AI Diagnosed',
};

function formatINR(val) {
  if (!val && val !== 0) return '—';
  return `₹ ${parseFloat(val).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
}

/**
 * Format a UTC/ISO date string into a short readable form.
 */
function formatDate(isoStr) {
  if (!isoStr) return 'Aug 26, 14:02';
  try {
    return new Date(isoStr).toLocaleDateString('en-IN', {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  } catch {
    return 'Aug 26, 14:02';
  }
}

/**
 * Cleanly truncate long raw IDs (e.g. order_rJ1inFTeoXT4ik -> order_rJ1in...)
 */
function truncateId(id) {
  if (!id || id === '—') return '—';
  if (id.length <= 15) return id;
  return `${id.slice(0, 11)}...`;
}

/**
 * Return the display amount for a settlement record.
 */
function getDisplayAmount(result) {
  if (result.settlement_credit !== undefined && result.settlement_credit !== null) {
    return result.settlement_credit;
  }
  if (result.amount !== undefined && result.amount !== null) {
    return result.amount;
  }
  return null;
}

function StatusBadge({ status, isResolved }) {
  if (isResolved) {
    return (
      <span className="status-subtle status-subtle--resolved" title="Resolved via AI Action">
        <span className="status-dot status-dot--green">●</span> Processed
      </span>
    );
  }
  if (status === 'matched') {
    return (
      <span className="status-subtle status-subtle--processed">
        <span className="status-dot status-dot--green">●</span> Processed
      </span>
    );
  }
  if (status === 'break') {
    return (
      <span className="rzp-badge rzp-badge--created">
        <AlertCircle size={10} /> 1 Break
      </span>
    );
  }
  return (
    <span className="status-subtle status-subtle--pending">
      <span className="status-dot status-dot--amber">●</span> Pending
    </span>
  );
}

function ExpandedDropdownCard({ result, language, onViewAI, isResolved }) {
  const explanation = language === 'hi'
    ? (result.explanation_hi || result.explanation_en)
    : result.explanation_en;

  return (
    <tr className="rzp-expanded-tr">
      <td colSpan={7}>
        <div className="rzp-dropdown-detail-card">
          <div className="dropdown-card-header">
            <span className="dropdown-card-title">
              Match Analysis — {PASS_LABELS[result.pass_number] || `Pass ${result.pass_number}`}
            </span>
            <span className="text-muted font-mono" style={{ fontSize: '11px' }}>
              Order ID: <code className="mono">{result.order_id}</code> | Settlement ID: <code className="mono">{result.settlement_id || '—'}</code>
            </span>
          </div>

          <div className="dropdown-card-grid">
            {/* Metadata Col */}
            <div className="dropdown-card-col">
              <div className="col-title">Execution Context</div>
              <div className="info-kv">
                <span className="kv-label">Recon Pass:</span>
                <span className="pass-tag-neutral">{result.pass_number}</span>
                <span className="kv-val font-semibold">{PASS_LABELS[result.pass_number]}</span>
              </div>
              <div className="info-kv">
                <span className="kv-label">Match Strategy:</span>
                <span className="kv-val">{result.pass_number === 1 ? 'Deterministic Hash' : result.pass_number === 2 ? 'Rule-Based Audit' : result.pass_number === 3 ? 'Heuristic Fuzzy' : 'LLM Diagnosis'}</span>
              </div>
              <div className="info-kv">
                <span className="kv-label">Status:</span>
                <span className="kv-val font-semibold">{result.status.toUpperCase()}</span>
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
        <td className="col-date">{formatDate(result.created_at)}</td>
        <td title={result.order_id}>
          <span className="font-mono text-xs text-slate-600">{truncateId(result.order_id)}</span>
        </td>
        <td title={result.settlement_id}>
          <span className="font-mono text-xs text-slate-500">{truncateId(result.settlement_id)}</span>
        </td>
        <td><StatusBadge status={result.status} isResolved={isResolved} /></td>
        <td>
          <span className="pass-tag-neutral" title={`Pass ${result.pass_number}`}>
            {result.pass_number}
          </span>
        </td>
        <td className="font-semibold text-right">
          {(() => {
            const amt = getDisplayAmount(result);
            return amt !== null ? formatINR(amt) : '—';
          })()}
        </td>
        <td>
          <button
            className="ghost-action-btn"
            onClick={e => { e.stopPropagation(); setExpanded(ex => !ex); }}
            title={expanded ? "Hide details" : "View match details"}
            aria-label="View match details"
          >
            {expanded ? <ChevronDown size={14} /> : <MoreHorizontal size={14} />}
          </button>
        </td>
      </tr>
      {expanded && <ExpandedDropdownCard result={result} language={language} onViewAI={onViewAI} isResolved={isResolved} />}
    </>
  );
}

export default function ReconWorkbench({ onOpenAI }) {
  const { state, dispatch, startRecon } = useReconciliation();
  const { results, activeTab, language, status, resolvedBreaks, searchQuery = '', statusFilter = 'all' } = state;

  const setSearchQuery = (query) => dispatch({ type: 'SET_SEARCH_QUERY', query });
  const setStatusFilter = (filter) => dispatch({ type: 'SET_STATUS_FILTER', filter });

  const breaks = useMemo(() => selectBreaks(results), [results]);
  const matched = useMemo(() => selectMatched(results), [results]);

  const filtered = useMemo(() => {
    let data = results || [];
    if (activeTab === 'matched') {
      data = (results || []).filter(r => r.status === 'matched' || resolvedBreaks.has(r.order_id));
    }
    if (activeTab === 'breaks') {
      data = breaks;
    }

    return data.filter(r => {
      const isResolved = resolvedBreaks.has(r.order_id);
      const rStatus = isResolved ? 'matched' : r.status;
      if (statusFilter !== 'all' && rStatus !== statusFilter) return false;

      if (searchQuery && searchQuery.trim()) {
        const q = searchQuery.trim().toLowerCase();

        const displayStatusText = isResolved
          ? 'resolved matched processed'
          : r.status === 'matched'
            ? 'processed matched'
            : r.status === 'break'
              ? 'break action required'
              : 'pending';

        const amt = getDisplayAmount(r);
        const formattedAmt = amt !== null ? formatINR(amt) : '';

        const searchableFields = [
          r.order_id,
          r.settlement_id,
          r.ledger_id,
          r.root_cause,
          r.pass_number ? `pass ${r.pass_number}` : '',
          r.pass_number,
          r.explanation_en,
          r.explanation_hi,
          r.suggested_action,
          r.severity,
          displayStatusText,
          r.created_at,
          amt,
          formattedAmt,
          Array.isArray(r.flags) ? r.flags.join(' ') : '',
          r.delta ? JSON.stringify(r.delta) : '',
        ];

        const isMatched = searchableFields.some(val =>
          val !== null && val !== undefined && String(val).toLowerCase().includes(q)
        );

        if (!isMatched) return false;
      }
      return true;
    });
  }, [results, activeTab, breaks, searchQuery, statusFilter, resolvedBreaks]);

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

  const matchedDisplayCount = matched.length + resolvedBreaks.size;
  const breaksDisplayCount = Math.max(0, breaks.length - resolvedBreaks.size);

  return (
    <div className="rzp-workbench-card card">
      {/* Integrated Single Toolbar Header */}
      <div className="rzp-single-toolbar">
        {/* Tabs Left */}
        <div className="rzp-tabs-group">
          {[
            { key: 'all', label: 'Settlements', count: results.length },
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
              {isLoading ? (
                <span className="sk-pill-sm" style={{ width: '28px', height: '16px', display: 'inline-block', marginLeft: '6px', verticalAlign: 'middle' }} />
              ) : (
                <span className={`rzp-tab-badge ${tab.key === 'breaks' ? 'rzp-tab-badge--break' : ''}`}>
                  {tab.count}
                </span>
              )}
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
        {state.error ? (
          <div className="workbench-empty-state">
            <AlertCircle size={36} className="empty-bot-icon text-red" />
            <h3 className="empty-title">Reconciliation Failed</h3>
            <p className="empty-desc text-red">{state.error}</p>
            <button className="btn btn-primary btn-sm" onClick={() => startRecon()} id="btn-retry-recon">
              <Play size={13} /> Retry Reconciliation Pipeline
            </button>
          </div>
        ) : isEmpty ? (
          <div className="rzp-hero-welcome">
            {/* Section Header */}
            <div className="hero-header-wrap">
              <h3 className="hero-title">
                Autonomous 4-Pass Reconciliation Engine
              </h3>
              <p className="hero-description">
                Audit payment gateway settlements against ERP ledgers using multi-pass deterministic rules, fuzzy heuristics, and LLM exception diagnostics.
              </p>
            </div>

            {/* Grid: 4 Equal-Height Cards */}
            <div className="hero-pipeline-grid">
              {/* Pass 1 Card */}
              <div className="pipeline-pass-card pass-card-1">
                <div>
                  <span className="pass-pill-badge badge-blue">Pass 1</span>
                  <div className="pass-card-title-group">
                    <h4 className="pass-card-main-title">Deterministic</h4>
                    <p className="pass-card-subtitle">Exact Match</p>
                  </div>
                </div>
                <p className="pass-card-desc">Matches Order ID &amp; net settlement amount with 100% precision.</p>
              </div>

              {/* Pass 2 Card */}
              <div className="pipeline-pass-card pass-card-2">
                <div>
                  <span className="pass-pill-badge badge-emerald">Pass 2</span>
                  <div className="pass-card-title-group">
                    <h4 className="pass-card-main-title">Contextual</h4>
                    <p className="pass-card-subtitle">Rule-Based Audit</p>
                  </div>
                </div>
                <p className="pass-card-desc">Audits MDR fee rates, 18% GST, and T+1/T+2 settlement timing lags.</p>
              </div>

              {/* Pass 3 Card */}
              <div className="pipeline-pass-card pass-card-3">
                <div>
                  <span className="pass-pill-badge badge-amber">Pass 3</span>
                  <div className="pass-card-title-group">
                    <h4 className="pass-card-main-title">Heuristic</h4>
                    <p className="pass-card-subtitle">Fuzzy Engine</p>
                  </div>
                </div>
                <p className="pass-card-desc">Reconciles cross-midnight batches, duplicate ERPs &amp; partial returns.</p>
              </div>

              {/* Pass 4 Card */}
              <div className="pipeline-pass-card pass-card-4">
                <div>
                  <span className="pass-pill-badge badge-purple">Pass 4</span>
                  <div className="pass-card-title-group">
                    <h4 className="pass-card-main-title">Llama 3.3 70B</h4>
                    <p className="pass-card-subtitle">AI Prescriber</p>
                  </div>
                </div>
                <p className="pass-card-desc">Diagnoses root causes and prescribes resolution steps for breaks.</p>
              </div>
            </div>

            {/* Action Button */}
            <div className="hero-cta-wrap">
              <button
                className="btn btn-primary hero-run-btn"
                onClick={() => startRecon()}
                disabled={isLoading}
                id="btn-run-recon-hero"
              >
                <Play size={15} fill="currentColor" />
                <span>Execute 4-Pass Reconciliation</span>
              </button>
            </div>
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
              {[...Array(10)].map((_, i) => (
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
