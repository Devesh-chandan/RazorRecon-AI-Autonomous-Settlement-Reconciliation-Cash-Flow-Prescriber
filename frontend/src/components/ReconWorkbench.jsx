import { useState, useMemo } from 'react';
import { ChevronDown, ChevronRight, Search, Bot, CheckCircle2, XCircle, Clock } from 'lucide-react';
import { useReconciliation, selectBreaks, selectMatched } from '../context/ReconciliationContext';
import './ReconWorkbench.css';

const PASS_LABELS = {
  1: 'Exact Match',
  2: 'Rule-Based',
  3: 'Fuzzy',
  4: 'AI Diagnosed',
};

const PASS_COLORS = {
  1: 'pass-1',
  2: 'pass-2',
  3: 'pass-3',
  4: 'pass-4',
};

function formatINR(val) {
  if (!val && val !== 0) return '—';
  return `₹${parseFloat(val).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
}

function StatusBadge({ status }) {
  if (status === 'matched') return <span className="badge badge-matched"><CheckCircle2 size={10} /> Matched</span>;
  if (status === 'break') return <span className="badge badge-break"><XCircle size={10} /> Break</span>;
  return <span className="badge badge-pending"><Clock size={10} /> Pending</span>;
}

function FlagList({ flags }) {
  if (!flags?.length) return null;
  return (
    <div className="flag-list">
      {flags.map(f => <span key={f} className="flag-tag">{f}</span>)}
    </div>
  );
}

function ExpandedRow({ result, language, onViewAI }) {
  const explanation = language === 'hi' ? result.explanation_hi : result.explanation_en;
  return (
    <tr className="expanded-row">
      <td colSpan={7}>
        <div className="expanded-content">
          <div className="expanded-grid">
            <div>
              <div className="expanded-section-title">Match Details</div>
              <dl className="expanded-dl">
                <dt>Pass</dt>
                <dd><span className={`pass-pill ${PASS_COLORS[result.pass_number]}`}>{result.pass_number}</span> {PASS_LABELS[result.pass_number]}</dd>
                <dt>Confidence</dt>
                <dd>{result.confidence != null ? `${(result.confidence * 100).toFixed(0)}%` : '—'}</dd>
                <dt>Settlement ID</dt>
                <dd className="mono">{result.settlement_id || '—'}</dd>
                <dt>Ledger ID</dt>
                <dd className="mono">{result.ledger_id || '—'}</dd>
              </dl>
            </div>
            {result.status === 'break' && (
              <div>
                <div className="expanded-section-title">AI Diagnosis</div>
                {result.root_cause && (
                  <div className="root-cause-tag">{result.root_cause?.replace(/_/g, ' ')}</div>
                )}
                {explanation && <p className="expanded-explanation">{explanation}</p>}
                {result.suggested_action && (
                  <p className="expanded-action"><strong>Action:</strong> {result.suggested_action}</p>
                )}
                <button
                  className="btn btn-ghost btn-sm view-ai-btn"
                  onClick={() => onViewAI(result)}
                  id={`view-ai-${result.order_id}`}
                >
                  <Bot size={12} /> View AI Analysis
                </button>
              </div>
            )}
            {Object.keys(result.delta || {}).length > 0 && (
              <div>
                <div className="expanded-section-title">Delta Values</div>
                <dl className="expanded-dl">
                  {Object.entries(result.delta).map(([k, v]) => (
                    <><dt key={`k-${k}`}>{k.replace(/_/g, ' ')}</dt><dd key={`v-${k}`} className="mono">{typeof v === 'number' ? formatINR(v) : String(v)}</dd></>
                  ))}
                </dl>
              </div>
            )}
          </div>
          <FlagList flags={result.flags} />
        </div>
      </td>
    </tr>
  );
}

function ResultRow({ result, language, onViewAI }) {
  const [expanded, setExpanded] = useState(false);
  const isBreak = result.status === 'break';

  return (
    <>
      <tr
        className={`result-row ${isBreak ? 'result-row--break' : ''} ${expanded ? 'result-row--expanded' : ''}`}
        onClick={() => setExpanded(e => !e)}
        id={`row-${result.order_id}`}
      >
        <td>
          {expanded ? <ChevronDown size={14} className="row-chevron" /> : <ChevronRight size={14} className="row-chevron" />}
        </td>
        <td className="mono truncate" style={{ maxWidth: 140 }} title={result.order_id}>{result.order_id}</td>
        <td><StatusBadge status={result.status} /></td>
        <td>
          <span className={`pass-pill ${PASS_COLORS[result.pass_number]}`}>
            {result.pass_number}
          </span>
        </td>
        <td className="mono">{result.confidence != null ? `${(result.confidence * 100).toFixed(0)}%` : '—'}</td>
        <td>
          {result.flags?.length > 0 ? (
            <span className="flag-tag">{result.flags[0]}{result.flags.length > 1 ? ` +${result.flags.length - 1}` : ''}</span>
          ) : '—'}
        </td>
        {isBreak && (
          <td>
            <button
              className="btn btn-ghost btn-sm"
              onClick={e => { e.stopPropagation(); onViewAI(result); }}
              id={`ai-btn-${result.order_id}`}
            >
              <Bot size={11} /> AI
            </button>
          </td>
        )}
        {!isBreak && <td />}
      </tr>
      {expanded && <ExpandedRow result={result} language={language} onViewAI={onViewAI} />}
    </>
  );
}

export default function ReconWorkbench() {
  const { state, dispatch } = useReconciliation();
  const { results, activeTab, language, status } = state;

  const [search, setSearch] = useState('');

  const breaks = useMemo(() => selectBreaks(results), [results]);
  const matched = useMemo(() => selectMatched(results), [results]);

  const tabData = {
    all: results,
    matched: matched,
    breaks: breaks,
  };

  const filtered = useMemo(() => {
    const data = tabData[activeTab] || [];
    if (!search) return data;
    const q = search.toLowerCase();
    return data.filter(r =>
      r.order_id?.toLowerCase().includes(q) ||
      r.settlement_id?.toLowerCase().includes(q) ||
      r.root_cause?.toLowerCase().includes(q)
    );
  }, [results, activeTab, search]);

  const onViewAI = (result) => {
    dispatch({ type: 'SELECT_BREAK', breakItem: result });
  };

  const isLoading = status === 'running';
  const isEmpty = status === 'idle' || (status !== 'running' && results.length === 0);

  return (
    <div className="recon-workbench card">
      {/* Tab Bar */}
      <div className="workbench-tabs" role="tablist">
        {[
          { key: 'all', label: 'All', count: results.length },
          { key: 'matched', label: 'Matched', count: matched.length },
          { key: 'breaks', label: 'Breaks', count: breaks.length },
        ].map(tab => (
          <button
            key={tab.key}
            id={`tab-${tab.key}`}
            role="tab"
            aria-selected={activeTab === tab.key}
            className={`workbench-tab ${activeTab === tab.key ? 'workbench-tab--active' : ''}`}
            onClick={() => dispatch({ type: 'SET_TAB', tab: tab.key })}
          >
            {tab.label}
            {tab.count > 0 && (
              <span className={`tab-count ${tab.key === 'breaks' && tab.count > 0 ? 'tab-count--breaks' : ''}`}>
                {tab.count}
              </span>
            )}
          </button>
        ))}

        {/* Search */}
        <div className="workbench-search">
          <Search size={13} className="search-icon" />
          <input
            id="recon-search"
            className="input search-input"
            placeholder="Search order ID, flag..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Table */}
      <div className="workbench-table-wrap">
        {isEmpty ? (
          <div className="workbench-empty">
            <Bot size={40} className="empty-icon" />
            <p>Run reconciliation to see results</p>
          </div>
        ) : isLoading && results.length === 0 ? (
          <div className="workbench-loading">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="skeleton" style={{ height: 48, marginBottom: 4, animationDelay: `${i * 80}ms` }} />
            ))}
          </div>
        ) : (
          <table className="workbench-table" aria-label="Reconciliation results">
            <thead>
              <tr>
                <th style={{ width: 24 }} />
                <th>Order ID</th>
                <th>Status</th>
                <th>Pass</th>
                <th>Confidence</th>
                <th>Flags</th>
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
                />
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={7} className="table-empty-row">No results match your search.</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
