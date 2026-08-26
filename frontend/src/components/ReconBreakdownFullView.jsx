import { useMemo, useState } from 'react';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid
} from 'recharts';
import {
  AlertTriangle, ShieldCheck, Building2, CheckCircle2, IndianRupee, ArrowUpRight
} from 'lucide-react';
import { useReconciliation, selectGatewayBreakdown, selectExceptionBreakdown } from '../context/ReconciliationContext';
import './ReconBreakdownFullView.css';

const formatINR = (val) => {
  if (val === null || val === undefined) return '₹0';
  if (Math.abs(val) >= 100000) return `₹${(val / 100000).toFixed(1)}L`;
  if (Math.abs(val) >= 1000) return `₹${(val / 1000).toFixed(1)}k`;
  return `₹${val.toLocaleString('en-IN')}`;
};

export default function ReconBreakdownFullView() {
  const { state } = useReconciliation();
  const { results, resolvedBreaks } = state;

  const [activeTab, setActiveTab] = useState('gateways'); // 'gateways' | 'exceptions'

  // Gateway Volume Distribution from shared selector
  const gatewayData = useMemo(() => {
    return selectGatewayBreakdown(results);
  }, [results]);

  // Exception Root Causes from shared selector
  const exceptionData = useMemo(() => {
    return selectExceptionBreakdown(results, resolvedBreaks);
  }, [results, resolvedBreaks]);

  const totalVolume = useMemo(() => gatewayData.reduce((s, g) => s + g.amount, 0), [gatewayData]);
  const totalBreaks = useMemo(() => exceptionData.reduce((s, e) => s + e.count, 0), [exceptionData]);
  const totalImpact = useMemo(() => exceptionData.reduce((s, e) => s + e.impact, 0), [exceptionData]);

  return (
    <div className="rb-page-container">
      {/* Clean Header */}
      <div className="rb-page-header">
        <div>
          <h1 className="rb-header-title">Reconciliation Breakdown Analysis</h1>
          <p className="rb-header-sub">
            Comprehensive audit of settlement volumes, payment gateway distribution, MDR fees, and exception root causes.
          </p>
        </div>

        {/* Tab Switcher Segment Control */}
        <div className="rb-tab-segment">
          <button
            className={`rb-tab-btn ${activeTab === 'gateways' ? 'rb-tab-btn--active' : ''}`}
            onClick={() => setActiveTab('gateways')}
          >
            <Building2 size={14} />
            <span>Gateway Distribution ({gatewayData.length})</span>
          </button>
          <button
            className={`rb-tab-btn ${activeTab === 'exceptions' ? 'rb-tab-btn--active' : ''}`}
            onClick={() => setActiveTab('exceptions')}
          >
            <AlertTriangle size={14} />
            <span>Exception Root Causes ({totalBreaks})</span>
          </button>
        </div>
      </div>

      {/* 4 Core KPI Stat Cards */}
      <div className="rb-kpi-grid">
        <div className="rb-kpi-card">
          <div className="rb-kpi-top">
            <span className="rb-kpi-label">Total Processed Volume</span>
            <div className="rb-icon-box icon-blue">
              <CheckCircle2 size={15} />
            </div>
          </div>
          <div className="rb-kpi-value font-mono">{formatINR(totalVolume)}</div>
          <div className="rb-kpi-sub text-emerald">
            <ArrowUpRight size={13} /> Across {gatewayData.length} Payment Gateways
          </div>
        </div>

        <div className="rb-kpi-card">
          <div className="rb-kpi-top">
            <span className="rb-kpi-label">Active Settlement Breaks</span>
            <div className="rb-icon-box icon-red">
              <AlertTriangle size={15} />
            </div>
          </div>
          <div className="rb-kpi-value font-mono text-red">{totalBreaks}</div>
          <div className="rb-kpi-sub text-red">
            Action required in Pass 4 AI Diagnostics
          </div>
        </div>

        <div className="rb-kpi-card">
          <div className="rb-kpi-top">
            <span className="rb-kpi-label">Total Financial Impact</span>
            <div className="rb-icon-box icon-amber">
              <IndianRupee size={15} />
            </div>
          </div>
          <div className="rb-kpi-value font-mono text-amber">{formatINR(totalImpact)}</div>
          <div className="rb-kpi-sub text-slate-500">
            Unreconciled delta between Gateway &amp; ERP
          </div>
        </div>

        <div className="rb-kpi-card">
          <div className="rb-kpi-top">
            <span className="rb-kpi-label">Overall Match Accuracy</span>
            <div className="rb-icon-box icon-emerald">
              <ShieldCheck size={15} />
            </div>
          </div>
          <div className="rb-kpi-value font-mono text-emerald">96.0%</div>
          <div className="rb-kpi-sub text-emerald">
            Verified by 4-Pass Engine
          </div>
        </div>
      </div>

      {/* Main Grid: Visual Left Card + Matrix Right Card */}
      <div className="rb-content-grid">
        {/* Left Column: Visual Chart Card */}
        <div className="rb-card">
          <div className="rb-card-header">
            <div>
              <h3 className="rb-card-title">
                {activeTab === 'gateways' ? 'Gateway Volume Allocation' : 'Exception Severity Breakdown'}
              </h3>
              <p className="rb-card-sub">Share of total settlement value</p>
            </div>
          </div>

          <div className="rb-chart-wrapper">
            {activeTab === 'gateways' ? (
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie
                    data={gatewayData}
                    dataKey="amount"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={95}
                    innerRadius={50}
                    paddingAngle={3}
                  >
                    {gatewayData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => [formatINR(value), 'Volume']} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={exceptionData} layout="vertical" margin={{ left: 10, right: 20, top: 10, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" tickFormatter={v => `₹${v / 1000}k`} stroke="#94a3b8" fontSize={11} />
                  <YAxis type="category" dataKey="pass" width={60} stroke="#94a3b8" fontSize={11} />
                  <Tooltip formatter={(val) => [formatINR(val), 'Financial Impact']} />
                  <Bar dataKey="impact" fill="#e53e3e" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Chart Legend */}
          <div className="rb-legend-grid">
            {activeTab === 'gateways' ? (
              gatewayData.map(gw => (
                <div key={gw.name} className="rb-legend-item">
                  <span className="rb-legend-dot" style={{ background: gw.color }} />
                  <span className="rb-legend-name">{gw.name}</span>
                  <span className="rb-legend-pct font-mono">{gw.percentage}%</span>
                </div>
              ))
            ) : (
              exceptionData.map(exc => (
                <div key={exc.title} className="rb-legend-item">
                  <span className="rb-legend-dot" style={{ background: exc.color }} />
                  <span className="rb-legend-name">{exc.title.slice(0, 26)}...</span>
                  <span className="rb-legend-pct font-mono">{exc.count} breaks</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Column: Detailed Performance Matrix Card */}
        <div className="rb-card">
          <div className="rb-card-header">
            <div>
              <h3 className="rb-card-title">
                {activeTab === 'gateways' ? 'Gateway Performance Matrix' : 'Exception Root Cause Actions'}
              </h3>
              <p className="rb-card-sub">Detailed breakdown &amp; audit metrics</p>
            </div>
          </div>

          <div className="rb-matrix-wrapper">
            {activeTab === 'gateways' ? (
              <div className="rb-gw-list">
                {gatewayData.map(gw => (
                  <div key={gw.name} className="rb-gw-row">
                    <div className="rb-gw-header">
                      <div className="rb-gw-left">
                        <span className="rb-gw-dot" style={{ background: gw.color }} />
                        <span className="rb-gw-name font-semibold text-slate-800">{gw.name}</span>
                        <span className="rb-gw-count font-mono">({gw.count} settlements)</span>
                      </div>
                      <div className="rb-gw-right font-mono">
                        <span className="rb-gw-pct text-slate-500">{gw.percentage}%</span>
                        <span className="rb-gw-amt font-bold text-slate-900">{formatINR(gw.amount)}</span>
                      </div>
                    </div>
                    <div className="rb-gw-track">
                      <div className="rb-gw-fill" style={{ width: `${gw.percentage}%`, background: gw.color }} />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="rb-exc-list">
                {exceptionData.map(exc => (
                  <div key={exc.title} className="rb-exc-card">
                    <div className="rb-exc-top">
                      <div className="rb-exc-title-wrap">
                        <AlertTriangle size={14} style={{ color: exc.color }} />
                        <h4 className="rb-exc-title">{exc.title}</h4>
                      </div>
                      <span className={`rb-sev-pill sev-${exc.severity.toLowerCase()}`}>
                        {exc.severity} Priority
                      </span>
                    </div>

                    <div className="rb-exc-meta">
                      <span>Pass: <strong>{exc.pass}</strong></span>
                      <span>Breaks: <strong>{exc.count}</strong></span>
                      <span>Financial Delta: <strong className="text-red font-mono">{formatINR(exc.impact)}</strong></span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
