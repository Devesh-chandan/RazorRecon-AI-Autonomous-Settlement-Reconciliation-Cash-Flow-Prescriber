import { useState } from 'react';
import {
  Layers, TrendingUp, Bot, ClipboardList, Download, HelpCircle, ChevronLeft, ChevronRight
} from 'lucide-react';
import { useReconciliation } from '../context/ReconciliationContext';
import { exportAuditLog } from '../api/client';
import './Sidebar.css';

export default function Sidebar({ onOpenAI, onOpenAudit, width = 220, isCollapsed = false, onToggleCollapse }) {
  const { state } = useReconciliation();
  const { runId, results, resolvedBreaks } = state;

  const [activeItem, setActiveItem] = useState('Settlements & Recon');

  const pass4Breaks = results.filter(r => r.status === 'break');
  const unresolvedCount = Math.max(0, pass4Breaks.length - resolvedBreaks.size);

  const handleNavClick = (item) => {
    setActiveItem(item.name);
    if (item.action) item.action();
  };

  const handleExport = () => {
    if (runId) {
      exportAuditLog(runId);
    } else {
      alert('Run reconciliation first to export audit logs.');
    }
  };

  const handleHelp = () => {
    window.open('http://localhost:8000/docs', '_blank');
  };

  const navGroups = [
    {
      title: 'RECONCILIATION ENGINE',
      items: [
        { name: 'Settlements & Recon', icon: Layers },
        { name: 'Cash Flow Forecast', icon: TrendingUp },
      ]
    },
    {
      title: 'AI DIAGNOSTICS & AUDIT',
      items: [
        {
          name: 'AI Diagnostics',
          icon: Bot,
          badge: unresolvedCount > 0 ? `${unresolvedCount}` : null,
          badgeType: 'ai',
          action: onOpenAI,
        },
        {
          name: 'Audit Trail & Logs',
          icon: ClipboardList,
          badge: results.length > 0 ? `${results.length}` : null,
          badgeType: 'audit',
          action: onOpenAudit,
        },
        { name: 'Export JSON Audit', icon: Download, action: handleExport },
      ]
    }
  ];

  return (
    <aside
      className={`rzp-sidebar ${isCollapsed ? 'rzp-sidebar--collapsed' : ''}`}
      id="app-sidebar"
      aria-label="Main Navigation"
      style={{ width: isCollapsed ? 64 : width, minWidth: isCollapsed ? 64 : width }}
    >
      {/* Logo Header + Collapse Toggle Button */}
      <div className="sidebar-logo-area">
        <div className="rzp-logo-badge" title="RazorRecon AI">
          <svg width="24" height="24" viewBox="0 0 32 32" fill="none">
            <rect width="32" height="32" rx="6" fill="#0B72E7"/>
            <path d="M8 10h10c2.2 0 4 1.8 4 4s-1.8 4-4 4h-6l5 4" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>

        {!isCollapsed && (
          <div className="rzp-brand-text">
            <span className="rzp-brand-name">RazorRecon</span>
            <span className="rzp-sub-brand">AI Engine</span>
          </div>
        )}

        <button
          className="sidebar-collapse-toggle-btn"
          onClick={onToggleCollapse}
          title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
          aria-label={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
        >
          {isCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="sidebar-nav">
        {navGroups.map((group, gIdx) => (
          <div key={gIdx} className="nav-group">
            {!isCollapsed && group.title && (
              <div className="nav-group-title">{group.title}</div>
            )}
            {group.items.map((item) => {
              const Icon = item.icon;
              const isActive = activeItem === item.name;
              return (
                <button
                  key={item.name}
                  className={`nav-item ${isActive ? 'nav-item--active' : ''}`}
                  onClick={() => handleNavClick(item)}
                  id={`nav-${item.name.toLowerCase().replace(/[^a-z0-9]/g, '-')}`}
                  title={isCollapsed ? item.name : undefined}
                >
                  {isActive && <span className="nav-active-bar" />}
                  <Icon size={16} className={`nav-icon ${item.badgeType === 'ai' ? 'nav-icon--ai' : ''}`} />
                  {!isCollapsed && <span className="nav-label">{item.name}</span>}
                  {item.badge && (
                    <span className={`nav-badge-pill ${item.badgeType === 'ai' ? 'nav-badge-pill--ai' : ''} ${isCollapsed ? 'nav-badge-pill--dot' : ''}`}>
                      {isCollapsed ? '' : item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Help & API Documentation Button */}
      <div className="sidebar-footer">
        <button
          className="help-support-btn"
          onClick={handleHelp}
          id="btn-help-support"
          title="API Documentation (Swagger)"
        >
          <HelpCircle size={14} />
          {!isCollapsed && <span>API Docs &amp; Help</span>}
        </button>
      </div>
    </aside>
  );
}
