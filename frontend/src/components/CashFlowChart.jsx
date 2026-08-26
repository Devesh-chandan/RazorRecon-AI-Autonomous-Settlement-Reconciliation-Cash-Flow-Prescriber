import { useMemo } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, ReferenceLine,
} from 'recharts';
import { TrendingUp, AlertTriangle } from 'lucide-react';
import { useReconciliation } from '../context/ReconciliationContext';
import './CashFlowChart.css';

function formatINR(value) {
  if (value === 0) return '₹0';
  if (value >= 100000) return `₹${(value / 100000).toFixed(1)}L`;
  if (value >= 1000) return `₹${(value / 1000).toFixed(1)}K`;
  return `₹${value.toFixed(0)}`;
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-date">{label}</div>
      {payload.map(p => (
        <div key={p.name} className="chart-tooltip-row" style={{ color: p.color }}>
          <span className="chart-tooltip-dot" style={{ background: p.color }} />
          <span>{p.name}:</span>
          <span className="chart-tooltip-val">{formatINR(p.value)}</span>
        </div>
      ))}
    </div>
  );
};

export default function CashFlowChart() {
  const { state } = useReconciliation();
  const { cashFlow, whatIfScenario, status } = state;

  const chartData = useMemo(() => {
    if (!cashFlow?.length) return [];

    // Find last index with non-zero activity
    let lastActiveIdx = cashFlow.length - 1;
    for (let i = cashFlow.length - 1; i >= 0; i--) {
      if ((cashFlow[i]?.confirmed_inflow || 0) > 0 || (cashFlow[i]?.disputed_held || 0) > 0) {
        lastActiveIdx = i;
        break;
      }
    }

    return cashFlow.map((day, i) => {
      const isFuture = i > lastActiveIdx && !whatIfScenario;

      const row = {
        date: day.day_label,
        'Confirmed Inflow': isFuture ? null : (day.confirmed_inflow ?? null),
        'Disputed / Held': isFuture ? null : (day.disputed_held ?? null),
      };

      if (whatIfScenario?.whatif_projection) {
        row['What-If'] = whatIfScenario.whatif_projection[i]?.confirmed_inflow ?? day.confirmed_inflow;
      }

      return row;
    });
  }, [cashFlow, whatIfScenario]);

  const totalConfirmed = (cashFlow || []).reduce((s, d) => s + (d?.confirmed_inflow || 0), 0);
  const totalDisputed = (cashFlow || []).reduce((s, d) => s + (d?.disputed_held || 0), 0);
  const whatIfGain = whatIfScenario
    ? (whatIfScenario.deltas || []).reduce((s, d) => s + (d?.delta || 0), 0)
    : 0;

  const isLoading = status === 'running';
  const isEmpty = !cashFlow?.length;

  return (
    <div className="cashflow-card card">
      <div className="cashflow-header">
        <div>
          <h2 className="cashflow-title">
            <TrendingUp size={16} />
            7-Day Cash Flow
          </h2>
        </div>
        {isLoading ? (
          <div style={{ display: 'flex', gap: '8px' }}>
            <div className="sk-pill sk-w-24" style={{ height: '22px' }} />
            <div className="sk-pill sk-w-24" style={{ height: '22px' }} />
          </div>
        ) : !isEmpty ? (
          <div className="cashflow-totals">
            <div className="cashflow-total cashflow-total--confirmed">
              <span>{formatINR(totalConfirmed)}</span>
              <span className="cashflow-total-label">confirmed</span>
            </div>
            {totalDisputed > 0 && (
              <div className="cashflow-total cashflow-total--disputed">
                <AlertTriangle size={12} />
                <span>{formatINR(totalDisputed)}</span>
                <span className="cashflow-total-label">disputed</span>
              </div>
            )}
          </div>
        ) : null}
      </div>

      {/* What-If Banner */}
      {whatIfScenario && whatIfGain > 0 && (
        <div className="whatif-banner" id="whatif-banner">
          <TrendingUp size={14} />
          <span>What-If: Resolving this break recovers <strong>{formatINR(whatIfGain)}</strong> in confirmed inflow.</span>
        </div>
      )}

      {/* Chart Area */}
      <div className="cashflow-chart-area">
        {isLoading ? (
          <div className="cashflow-skeleton-container" style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '12px 16px', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', height: '145px', gap: '14px' }}>
              {[60, 85, 45, 95, 70, 80, 65].map((h, i) => (
                <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', height: '100%', justifyContent: 'flex-end' }}>
                  <div className="sk-box" style={{ width: '100%', height: `${h}%`, borderRadius: '4px 4px 0 0' }} />
                  <div className="sk-box" style={{ width: '30px', height: '10px' }} />
                </div>
              ))}
            </div>
          </div>
        ) : isEmpty ? (
          <div className="cashflow-empty">
            <TrendingUp size={40} className="empty-icon" />
            <p>Run reconciliation to see the 7-day projection</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="gradConfirmed" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#1cb468" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#1cb468" stopOpacity={0.02} />
                </linearGradient>
                <linearGradient id="gradDisputed" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#e8960c" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#e8960c" stopOpacity={0.02} />
                </linearGradient>
                <linearGradient id="gradWhatif" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2D81E0" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#2D81E0" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: 'var(--text-tertiary)' }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 11, fill: 'var(--text-tertiary)' }}
                tickFormatter={formatINR}
                axisLine={false}
                tickLine={false}
                width={55}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                iconType="circle"
                iconSize={8}
                wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
              />

              <Area
                type="monotone"
                dataKey="Confirmed Inflow"
                stroke="#1cb468"
                strokeWidth={2}
                fill="url(#gradConfirmed)"
                animationDuration={1500}
                dot={false}
                activeDot={{ r: 4, strokeWidth: 0 }}
                connectNulls={false}
              />
              <Area
                type="monotone"
                dataKey="Disputed / Held"
                stroke="#e8960c"
                strokeWidth={2}
                fill="url(#gradDisputed)"
                animationDuration={1500}
                dot={false}
                activeDot={{ r: 4, strokeWidth: 0 }}
                connectNulls={false}
              />
              {whatIfScenario && (
                <Area
                  type="monotone"
                  dataKey="What-If"
                  stroke="#2D81E0"
                  strokeWidth={2}
                  strokeDasharray="6 3"
                  fill="url(#gradWhatif)"
                  animationDuration={800}
                  dot={false}
                  activeDot={{ r: 4, strokeWidth: 0 }}
                  connectNulls={false}
                />
              )}
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
