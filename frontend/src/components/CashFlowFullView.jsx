import { useMemo, useState } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import {
  TrendingUp, AlertCircle, CheckCircle2, ShieldAlert, ArrowUpRight, Calendar
} from 'lucide-react';
import { useReconciliation } from '../context/ReconciliationContext';
import './CashFlowFullView.css';

const formatINR = (val) => {
  if (val === null || val === undefined) return '₹0';
  if (Math.abs(val) >= 100000) return `₹${(val / 100000).toFixed(1)}L`;
  if (Math.abs(val) >= 1000) return `₹${(val / 1000).toFixed(1)}k`;
  return `₹${val.toLocaleString('en-IN')}`;
};

export default function CashFlowFullView() {
  const { state } = useReconciliation();
  const { cashFlow, whatIfScenario, status } = state;

  const [simulatedResolution, setSimulatedResolution] = useState(true);

  // Compute live data directly from cashFlow
  const totalConfirmed = useMemo(() => {
    return (cashFlow || []).reduce((s, d) => s + (d?.confirmed_inflow || 0), 0);
  }, [cashFlow]);

  const totalDisputed = useMemo(() => {
    return (cashFlow || []).reduce((s, d) => s + (d?.disputed_held || 0), 0);
  }, [cashFlow]);

  const projectedRecovery = useMemo(() => {
    return Math.round(totalDisputed * 0.85);
  }, [totalDisputed]);

  const chartData = useMemo(() => {
    if (!cashFlow?.length) return [];

    let lastActiveIdx = cashFlow.length - 1;
    for (let i = cashFlow.length - 1; i >= 0; i--) {
      if ((cashFlow[i]?.confirmed_inflow || 0) > 0 || (cashFlow[i]?.disputed_held || 0) > 0) {
        lastActiveIdx = i;
        break;
      }
    }

    return cashFlow.map((day, i) => {
      const isFuture = i > lastActiveIdx && !whatIfScenario;

      const baseInflow = day.confirmed_inflow || 0;
      const disputedAmt = day.disputed_held || 0;
      const simulatedGain = simulatedResolution ? Math.round(disputedAmt * 0.85) : 0;

      return {
        date: day.day_label,
        'Confirmed Inflow': isFuture ? null : baseInflow,
        'Disputed / Held': isFuture ? null : disputedAmt,
        'Simulated Recovery': isFuture ? null : baseInflow + simulatedGain,
      };
    });
  }, [cashFlow, whatIfScenario, simulatedResolution]);

  const isLoading = status === 'running';

  return (
    <div className="cf-page-container">
      {/* Clean Single Header */}
      <div className="cf-page-header">
        <div>
          <h1 className="cf-header-title">7-Day Cash Flow Projection &amp; Recovery Analysis</h1>
          <p className="cf-header-sub">
            Real-time liquidity forecasting based on settlement clearance, gateway holdbacks, and AI exception resolution.
          </p>
        </div>

        <button
          className={`cf-toggle-btn ${simulatedResolution ? 'cf-toggle-btn--active' : ''}`}
          onClick={() => setSimulatedResolution(prev => !prev)}
          title="Toggle AI Recovery Simulation"
        >
          <ShieldAlert size={15} />
          <span>Simulate AI Recovery (+{formatINR(projectedRecovery)})</span>
        </button>
      </div>

      {/* 3 Core KPI Metric Cards */}
      <div className="cf-kpi-grid">
        <div className="cf-kpi-card">
          <div className="cf-kpi-top">
            <span className="cf-kpi-label">7-Day Confirmed Inflow</span>
            <CheckCircle2 size={16} className="cf-icon-emerald" />
          </div>
          <div className="cf-kpi-value font-mono">{formatINR(totalConfirmed)}</div>
          <div className="cf-kpi-sub text-emerald">
            <ArrowUpRight size={13} /> Verified by Pass 1 &amp; Pass 2
          </div>
        </div>

        <div className="cf-kpi-card">
          <div className="cf-kpi-top">
            <span className="cf-kpi-label">Disputed / Held in Exceptions</span>
            <AlertCircle size={16} className="cf-icon-amber" />
          </div>
          <div className="cf-kpi-value font-mono text-amber">{formatINR(totalDisputed)}</div>
          <div className="cf-kpi-sub text-slate-500">
            Holdbacks due to fee discrepancies &amp; timing lags
          </div>
        </div>

        <div className="cf-kpi-card cf-kpi-card--highlight">
          <div className="cf-kpi-top">
            <span className="cf-kpi-label">Projected AI Recovery Gain</span>
            <TrendingUp size={16} className="cf-icon-blue" />
          </div>
          <div className="cf-kpi-value font-mono text-blue">{formatINR(projectedRecovery)}</div>
          <div className="cf-kpi-sub text-blue font-semibold">
            +85% potential liquidity unlock upon AI resolution
          </div>
        </div>
      </div>

      {/* Streamlined Chart Card */}
      <div className="cf-card">
        <div className="cf-card-header">
          <h2 className="cf-card-title">Cash Inflow Trend &amp; Scenario Projection</h2>
          <div className="cf-legend-group">
            <span className="cf-legend legend-confirmed">● Confirmed Inflow</span>
            <span className="cf-legend legend-disputed">● Disputed / Held</span>
            {simulatedResolution && <span className="cf-legend legend-simulated">-- AI Recovery</span>}
          </div>
        </div>

        <div className="cf-chart-wrap">
          {isLoading ? (
            <div className="cf-chart-loading">
              <div className="sk-box" style={{ width: '100%', height: '280px', borderRadius: '6px' }} />
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={chartData} margin={{ top: 15, right: 20, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="cfGradConfirmed" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#1cb468" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#1cb468" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="cfGradDisputed" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#e8960c" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#e8960c" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="cfGradSimulated" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0b72e7" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#0b72e7" stopOpacity={0.0} />
                  </linearGradient>
                </defs>

                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={{ stroke: '#e2e8f0' }} />
                <YAxis
                  stroke="#94a3b8"
                  fontSize={11}
                  tickFormatter={val => `₹${val / 1000}k`}
                  axisLine={false}
                  tickLine={false}
                  width={50}
                />
                <Tooltip
                  formatter={(value) => [formatINR(value), '']}
                  contentStyle={{ background: '#ffffff', borderRadius: 6, border: '1px solid #e2e8f0', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}
                />

                <Area
                  type="monotone"
                  dataKey="Confirmed Inflow"
                  stroke="#1cb468"
                  strokeWidth={2}
                  fill="url(#cfGradConfirmed)"
                  connectNulls={false}
                />
                <Area
                  type="monotone"
                  dataKey="Disputed / Held"
                  stroke="#e8960c"
                  strokeWidth={2}
                  fill="url(#cfGradDisputed)"
                  connectNulls={false}
                />
                {simulatedResolution && (
                  <Area
                    type="monotone"
                    dataKey="Simulated Recovery"
                    stroke="#0b72e7"
                    strokeWidth={2}
                    strokeDasharray="4 4"
                    fill="url(#cfGradSimulated)"
                    connectNulls={false}
                  />
                )}
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Streamlined Daily Inflow Table */}
      <div className="cf-card">
        <div className="cf-card-header">
          <h3 className="cf-card-title"><Calendar size={14} /> Daily Liquidity Breakdown</h3>
          <span className="cf-card-tag font-mono">{cashFlow?.length || 0} Projection Days</span>
        </div>

        <div className="cf-table-wrap">
          <table className="cf-table">
            <thead>
              <tr>
                <th>Date / Day</th>
                <th className="text-right">Confirmed Inflow</th>
                <th className="text-right">Disputed / Held</th>
                <th className="text-right">Simulated AI Gain</th>
                <th className="text-right">Net Projected Total</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {(cashFlow || []).map((day, idx) => {
                const confirmed = day.confirmed_inflow || 0;
                const disputed = day.disputed_held || 0;
                const simGain = simulatedResolution ? Math.round(disputed * 0.85) : 0;
                const net = confirmed + simGain;

                return (
                  <tr key={idx}>
                    <td className="font-semibold text-slate-800">{day.day_label}</td>
                    <td className="text-right font-mono text-emerald">{formatINR(confirmed)}</td>
                    <td className="text-right font-mono text-amber">{formatINR(disputed)}</td>
                    <td className="text-right font-mono text-blue">{formatINR(simGain)}</td>
                    <td className="text-right font-mono font-bold text-slate-900">{formatINR(net)}</td>
                    <td>
                      <span className={`cf-status-pill ${disputed > 0 ? 'cf-pill-amber' : 'cf-pill-emerald'}`}>
                        {disputed > 0 ? 'Holds Pending' : 'Cleared'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
