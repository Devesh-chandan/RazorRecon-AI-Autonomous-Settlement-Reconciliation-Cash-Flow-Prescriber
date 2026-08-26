import { useState, useMemo } from 'react';
import { Layers, AlertTriangle, ShieldCheck, PieChart } from 'lucide-react';
import { useReconciliation, selectGatewayBreakdown, selectExceptionBreakdown } from '../context/ReconciliationContext';
import './GatewayBreakdownWidget.css';

function formatINR(value) {
  if (!value && value !== 0) return '₹0';
  if (value >= 100000) return `₹${(value / 100000).toFixed(1)}L`;
  if (value >= 1000) return `₹${(value / 1000).toFixed(1)}k`;
  return `₹${value.toFixed(0)}`;
}

export default function GatewayBreakdownWidget() {
  const { state } = useReconciliation();
  const { results, resolvedBreaks, status } = state;
  const [activeTab, setActiveTab] = useState('gateways'); // 'gateways' | 'exceptions'

  const isLoading = status === 'running';
  const isEmpty = status === 'idle' && (!results || results.length === 0);

  const gatewayData = useMemo(() => {
    return selectGatewayBreakdown(results);
  }, [results]);

  const exceptionData = useMemo(() => {
    return selectExceptionBreakdown(results, resolvedBreaks);
  }, [results, resolvedBreaks]);

  return (
    <div className="gateway-widget-card card">
      {/* Widget Header */}
      <div className="gateway-widget-header">
        <div className="gateway-header-left">
          <Layers size={15} className="text-blue" />
          <h3 className="gateway-widget-title">Reconciliation Breakdown</h3>
        </div>
        <div className="gateway-tab-toggle">
          <button
            className={`gateway-tab-btn ${activeTab === 'gateways' ? 'active' : ''}`}
            onClick={() => setActiveTab('gateways')}
          >
            Gateways
          </button>
          <button
            className={`gateway-tab-btn ${activeTab === 'exceptions' ? 'active' : ''}`}
            onClick={() => setActiveTab('exceptions')}
          >
            Exceptions
          </button>
        </div>
      </div>

      {/* Widget Content Body */}
      <div className="gateway-widget-body">
        {isLoading ? (
          <div className="gateway-skeleton-list">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="gateway-skeleton-item-stacked">
                <div className="skeleton-row-top">
                  <div className="sk-box sk-w-32" />
                  <div className="sk-box sk-w-24" />
                </div>
                <div className="sk-box" style={{ width: '100%', height: '6px', borderRadius: '3px' }} />
              </div>
            ))}
          </div>
        ) : isEmpty ? (
          <div className="gateway-empty-state">
            <PieChart size={32} className="gateway-empty-icon" />
            <p>Run reconciliation to view gateway distribution &amp; exception breakdown</p>
          </div>
        ) : activeTab === 'gateways' ? (
          <div className="gateway-list">
            {gatewayData.map(gw => (
              <div key={gw.name} className="gateway-item-stacked">
                <div className="gateway-top-row">
                  <div className="gateway-info-left">
                    <span className="gateway-color-dot" style={{ background: gw.color }} />
                    <span className="gateway-name">{gw.name}</span>
                    <span className="gateway-count font-mono">({gw.count})</span>
                  </div>
                  <div className="gateway-stats-right">
                    <span className="gateway-pct font-mono">{gw.percentage}%</span>
                    <span className="gateway-amt font-mono">{formatINR(gw.amount)}</span>
                  </div>
                </div>
                <div className="gateway-bar-track">
                  <div
                    className="gateway-bar-fill"
                    style={{ width: `${gw.percentage}%`, background: gw.color }}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="exceptions-list">
            {exceptionData.map(exc => (
              <div key={exc.title} className="exception-row">
                <div className="exception-header">
                  <div className="exception-title-wrap">
                    <AlertTriangle size={13} style={{ color: exc.color }} />
                    <span className="exception-title">{exc.title}</span>
                  </div>
                  <span className={`exception-badge badge-${exc.severity?.toLowerCase() || 'medium'}`}>
                    {exc.count} {exc.count === 1 ? 'break' : 'breaks'}
                  </span>
                </div>
                <div className="exception-impact-row">
                  <span className="text-tertiary">Financial Impact:</span>
                  <span className="exception-amt font-mono text-red">{formatINR(exc.impact)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
