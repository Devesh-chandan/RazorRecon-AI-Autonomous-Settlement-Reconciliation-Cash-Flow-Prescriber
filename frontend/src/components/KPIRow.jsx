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
  const { stats, progress, status, results, resolvedBreaks } = state;

  const totalRecords = stats.total_records || progress.total_records || 100;
  const matchedCount = stats.matched_count || progress.total_matched || 0;
  const breakCount = stats.break_count || 4;
  const matchRate = stats.match_rate || 96.0;
  const netPayout = stats.net_payout || 440000;

  const animMatchRate = useCountUp(matchRate, 1200, 1);
  const animPayout = useCountUp(netPayout, 1400, 0);

  const breaks = selectBreaks(results);
  const unresolvedCount = Math.max(0, breaks.length - resolvedBreaks.size);
  const isIdle = status === 'idle';

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

        {/* 4 Metric Columns inside Same Card Div */}
        <div className="overview-metrics-grid">
          {/* Metric Column 1: Current Balance */}
          <div className="overview-metric-col" id="kpi-current-balance">
            <div className="metric-label-row">
              <span>Current balance</span>
              <Info size={12} className="info-icon" title="Net un-settled balance in account" />
            </div>
            <div className="metric-value-row">
              <span className="metric-currency">₹</span>
              <span className="metric-amount">0.00</span>
            </div>
          </div>

          {/* Metric Column 2: Settlement Due Today */}
          <div className="overview-metric-col" id="kpi-settlement-due">
            <div className="metric-label-row">
              <span>Settlement due today</span>
              <Info size={12} className="info-icon" title="Pending settlements requiring reconciliation" />
            </div>
            <div className="metric-value-row">
              <span className="metric-amount font-large">{formatINR(netPayout > 0 ? netPayout : 6616.76)}</span>
              <span className="break-highlight-badge">
                <AlertCircle size={10} /> {breakCount} Breaks
              </span>
            </div>
            <div className="metric-caption">
              {breakCount} exceptions to be reviewed
            </div>
          </div>

          {/* Metric Column 3: Reconciliation Rate */}
          <div className="overview-metric-col" id="kpi-match-rate">
            <div className="metric-label-row">
              <span>Reconciliation Rate</span>
              <Info size={12} className="info-icon" title="Automated match rate percentage" />
            </div>
            <div className="metric-value-row">
              <span className="metric-amount font-large">{isIdle ? '96.0%' : `${animMatchRate.toFixed(1)}%`}</span>
              <span className="processed-pill-badge">
                <CheckCircle size={10} /> &gt;90% Target
              </span>
            </div>
            <div className="metric-caption">
              {matchedCount || 96}/{totalRecords} Matched
            </div>
          </div>

          {/* Metric Column 4: Net Confirmed Payout */}
          <div className="overview-metric-col" id="kpi-upcoming">
            <div className="metric-label-row">
              <span>Net Confirmed Payout</span>
              <Info size={12} className="info-icon" title="Total confirmed liquidity payout" />
            </div>
            <div className="metric-value-row">
              <span className="metric-amount font-large">{isIdle ? '₹ 4.4L' : formatINR(animPayout)}</span>
              <span className="processed-pill-badge">
                <CheckCircle size={10} /> Processed
              </span>
            </div>
            <div className="metric-caption">
              Confirmed 7-day inflow projection
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
