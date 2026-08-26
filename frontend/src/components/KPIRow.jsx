import { useEffect, useRef, useState } from 'react';
import { Info, RefreshCw, CheckCircle, Bot, ClipboardList, AlertCircle } from 'lucide-react';
import { useReconciliation, selectBreaks } from '../context/ReconciliationContext';
import './KPIRow.css';

function useCountUp(target, duration = 1200, decimals = 0) {
  const [current, setCurrent] = useState(0);
  const rafRef = useRef(null);
  const startRef = useRef(null);

  useEffect(() => {
    if (target === 0) { setCurrent(0); return; }
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    startRef.current = null;

    const step = (timestamp) => {
      if (!startRef.current) startRef.current = timestamp;
      const elapsed = timestamp - startRef.current;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setCurrent(parseFloat((eased * target).toFixed(decimals)));
      if (progress < 1) rafRef.current = requestAnimationFrame(step);
    };

    rafRef.current = requestAnimationFrame(step);
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, [target, duration, decimals]);

  return current;
}

function formatINR(value) {
  if (value >= 100000) return `₹ ${(value / 100000).toFixed(2)}L`;
  if (value >= 1000) return `₹ ${(value / 1000).toFixed(2)}K`;
  return `₹ ${value.toFixed(2)}`;
}

export default function KPIRow({ onOpenAI, onOpenAudit }) {
  const { state, refreshData } = useReconciliation();
  const { stats = {}, progress = {}, status, results = [], resolvedBreaks = new Set() } = state || {};

  const breaks = selectBreaks(results);
  const matched = results.filter(r => r && r.status === 'matched');

  const hasData = results.length > 0 || stats.total_records != null;

  const totalRecords = stats.total_records ?? progress.total_records ?? (results.length > 0 ? results.length : 0);
  const matchedCount = stats.matched_count ?? progress.total_matched ?? (results.length > 0 ? matched.length + resolvedBreaks.size : 0);
  const breakCount = stats.break_count ?? (results.length > 0 ? Math.max(0, breaks.length - resolvedBreaks.size) : 0);
  const rawMatchRate = totalRecords > 0 ? parseFloat(((matchedCount / totalRecords) * 100).toFixed(1)) : 0.0;
  const matchRate = stats.match_rate ?? (results.length > 0 ? rawMatchRate : 0.0);
  const netPayout = stats.net_payout ?? (results.length > 0 ? 440000 : 0);

  const animMatchRate = useCountUp(hasData ? matchRate : 0, 1200, 1);
  const animPayout = useCountUp(hasData ? netPayout : 0, 1400, 0);

  const unresolvedCount = Math.max(0, breaks.length - resolvedBreaks.size);

  return (
    <section className="rzp-overview-section" aria-label="Settlement Overview">
      {/* Extended Single Card Div Container */}
      <div className="rzp-overview-card">
        {/* Top Control Bar inside Single Div */}
        <div className="overview-card-header-bar">
          <div className="overview-title-group">
            <h2 className="overview-title">Overview</h2>
            <span className="overview-timestamp">Just now</span>
            <button
              className="overview-refresh-btn"
              onClick={refreshData}
              disabled={status === 'running'}
              title="Refresh Settlements & Data"
            >
              <RefreshCw size={12} className={status === 'running' ? 'animate-spin' : ''} />
              <span>Refresh</span>
            </button>
          </div>

          <div className="overview-links-group">
            <button className="overview-action-link" onClick={onOpenAI} id="btn-overview-ai">
              <Bot size={13} className="text-blue" />
              <span>AI Exception Analysis</span>
              {unresolvedCount > 0 && <span className="overview-link-badge">{unresolvedCount}</span>}
            </button>
            <span className="overview-link-divider">|</span>
            <button className="overview-action-link" onClick={onOpenAudit} id="btn-overview-audit">
              <ClipboardList size={13} className="text-blue" />
              <span>Audit Logs</span>
            </button>
          </div>
        </div>

        {/* 4 Metric Card Containers */}
        <div className="overview-metrics-grid">
          {/* Metric Column 1: Current Balance */}
          <div className="overview-metric-col" id="kpi-current-balance">
            <div className="metric-label-row">
              <span>Current balance</span>
              <Info size={12} className="info-icon" title="Net un-settled balance in account" />
            </div>
            {status === 'running' ? (
              <div className="metric-value-row">
                <div className="sk-box sk-w-20" style={{ height: '24px', margin: '4px 0' }} />
              </div>
            ) : !hasData ? (
              <>
                <div className="metric-value-row">
                  <span className="metric-amount font-large" style={{ color: '#a0aec0' }}>—</span>
                </div>
                <div className="metric-caption">
                  Awaiting Reconciliation
                </div>
              </>
            ) : (
              <>
                <div className="metric-value-row">
                  <span className="metric-currency">₹</span>
                  <span className="metric-amount">0.00</span>
                  <span className="processed-pill-badge">
                    <CheckCircle size={10} /> Available
                  </span>
                </div>
                <div className="metric-caption">
                  Escrow Account Balance
                </div>
              </>
            )}
          </div>

          {/* Metric Column 2: Settlement Due Today */}
          <div className="overview-metric-col" id="kpi-settlement-due">
            <div className="metric-label-row">
              <span>Settlement due today</span>
              <Info size={12} className="info-icon" title="Pending settlements requiring reconciliation" />
            </div>
            {status === 'running' ? (
              <>
                <div className="metric-value-row" style={{ gap: '8px', alignItems: 'center' }}>
                  <div className="sk-box sk-w-32" style={{ height: '24px' }} />
                  <div className="sk-pill sk-w-24" style={{ height: '18px' }} />
                </div>
                <div className="sk-box sk-w-24" style={{ height: '11px', marginTop: '6px' }} />
              </>
            ) : !hasData ? (
              <>
                <div className="metric-value-row">
                  <span className="metric-amount font-large" style={{ color: '#a0aec0' }}>—</span>
                </div>
                <div className="metric-caption">
                  Awaiting Reconciliation
                </div>
              </>
            ) : (
              <>
                <div className="metric-value-row">
                  <span className="metric-amount font-large">{formatINR(netPayout)}</span>
                  <span className="break-highlight-badge">
                    <AlertCircle size={10} /> {breakCount} Breaks
                  </span>
                </div>
                <div className="metric-caption">
                  {breakCount} exceptions to be reviewed
                </div>
              </>
            )}
          </div>

          {/* Metric Column 3: Reconciliation Rate */}
          <div className="overview-metric-col" id="kpi-match-rate">
            <div className="metric-label-row">
              <span>Reconciliation Rate</span>
              <Info size={12} className="info-icon" title="Automated match rate percentage" />
            </div>
            {status === 'running' ? (
              <>
                <div className="metric-value-row" style={{ gap: '8px', alignItems: 'center' }}>
                  <div className="sk-box sk-w-20" style={{ height: '24px' }} />
                  <div className="sk-pill sk-w-24" style={{ height: '18px' }} />
                </div>
                <div className="sk-box sk-w-24" style={{ height: '11px', marginTop: '6px' }} />
              </>
            ) : !hasData ? (
              <>
                <div className="metric-value-row">
                  <span className="metric-amount font-large" style={{ color: '#a0aec0' }}>—</span>
                </div>
                <div className="metric-caption">
                  0/0 Matched
                </div>
              </>
            ) : (
              <>
                <div className="metric-value-row">
                  <span className="metric-amount font-large">{`${animMatchRate.toFixed(1)}%`}</span>
                  <span className="processed-pill-badge">
                    <CheckCircle size={10} /> &gt;90% Target
                  </span>
                </div>
                <div className="metric-caption">
                  {matchedCount}/{totalRecords} Matched
                </div>
              </>
            )}
          </div>

          {/* Metric Column 4: Net Confirmed Payout */}
          <div className="overview-metric-col" id="kpi-upcoming">
            <div className="metric-label-row">
              <span>Net Confirmed Payout</span>
              <Info size={12} className="info-icon" title="Total confirmed liquidity payout" />
            </div>
            {status === 'running' ? (
              <>
                <div className="metric-value-row" style={{ gap: '8px', alignItems: 'center' }}>
                  <div className="sk-box sk-w-32" style={{ height: '24px' }} />
                  <div className="sk-pill sk-w-24" style={{ height: '18px' }} />
                </div>
                <div className="sk-box sk-w-32" style={{ height: '11px', marginTop: '6px' }} />
              </>
            ) : !hasData ? (
              <>
                <div className="metric-value-row">
                  <span className="metric-amount font-large" style={{ color: '#a0aec0' }}>—</span>
                </div>
                <div className="metric-caption">
                  Awaiting Pipeline Run
                </div>
              </>
            ) : (
              <>
                <div className="metric-value-row">
                  <span className="metric-amount font-large">{formatINR(animPayout)}</span>
                  <span className="processed-pill-badge">
                    <CheckCircle size={10} /> Processed
                  </span>
                </div>
                <div className="metric-caption">
                  Confirmed 7-day inflow projection
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
