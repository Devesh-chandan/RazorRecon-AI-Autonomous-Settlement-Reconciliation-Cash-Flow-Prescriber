import { useEffect, useRef, useState } from 'react';
import { BarChart2, CheckCircle, AlertCircle, DollarSign, TrendingUp } from 'lucide-react';
import { useReconciliation } from '../context/ReconciliationContext';
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
      // Ease-out cubic
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
  if (value >= 100000) return `₹${(value / 100000).toFixed(1)}L`;
  if (value >= 1000) return `₹${(value / 1000).toFixed(1)}K`;
  return `₹${value.toFixed(0)}`;
}

function KPICard({ id, icon: Icon, label, value, displayValue, color, delta, subtitle, index }) {
  return (
    <div
      id={id}
      className={`kpi-card animate-fadeInUp stagger-${index + 1}`}
      style={{ '--kpi-color': color }}
    >
      <div className="kpi-top-border" />
      <div className="kpi-header">
        <div className="kpi-icon" style={{ background: `${color}15` }}>
          <Icon size={18} color={color} />
        </div>
        {delta !== undefined && (
          <span className={`kpi-delta ${delta >= 0 ? 'kpi-delta--up' : 'kpi-delta--down'}`}>
            <TrendingUp size={10} />
            {delta >= 0 ? '+' : ''}{delta}%
          </span>
        )}
      </div>
      <div className="kpi-value">{displayValue}</div>
      <div className="kpi-label">{label}</div>
      {subtitle && <div className="kpi-subtitle">{subtitle}</div>}
    </div>
  );
}

export default function KPIRow() {
  const { state } = useReconciliation();
  const { stats, progress, status, results } = state;

  const totalRecords = stats.total_records || progress.total_records || 100;
  const matchedCount = stats.matched_count || progress.total_matched || 0;
  const breakCount = stats.break_count || 0;
  const matchRate = stats.match_rate || 0;
  const netPayout = stats.net_payout || 0;

  const animMatchRate = useCountUp(matchRate, 1200, 1);
  const animMatched = useCountUp(matchedCount, 1000, 0);
  const animBreaks = useCountUp(breakCount, 800, 0);
  const animPayout = useCountUp(netPayout, 1400, 0);

  const isIdle = status === 'idle';

  return (
    <section className="kpi-row" aria-label="Key Performance Indicators">
      <KPICard
        id="kpi-total"
        index={0}
        icon={BarChart2}
        label="Total Transactions"
        value={totalRecords}
        displayValue={isIdle ? '—' : totalRecords.toLocaleString()}
        color="var(--primary)"
        subtitle="Settlement records"
      />
      <KPICard
        id="kpi-match-rate"
        index={1}
        icon={CheckCircle}
        label="Match Rate"
        value={animMatchRate}
        displayValue={isIdle ? '—' : `${animMatchRate.toFixed(1)}%`}
        color="var(--success)"
        delta={status === 'complete' ? (matchRate >= 90 ? 90 : 0) : undefined}
        subtitle="Target: >90%"
      />
      <KPICard
        id="kpi-breaks"
        index={2}
        icon={AlertCircle}
        label="Breaks"
        value={animBreaks}
        displayValue={isIdle ? '—' : Math.round(animBreaks).toString()}
        color="var(--error)"
        subtitle="Require review"
      />
      <KPICard
        id="kpi-payout"
        index={3}
        icon={DollarSign}
        label="Net Payout"
        value={animPayout}
        displayValue={isIdle ? '—' : formatINR(animPayout)}
        color="var(--primary)"
        subtitle="Confirmed inflow"
      />
    </section>
  );
}
