import { useState } from 'react';
import { Play, RefreshCw, Activity, Search, User, ChevronDown, UploadCloud, Globe, Code } from 'lucide-react';
import { useReconciliation } from '../context/ReconciliationContext';
import { DOCS_URL } from '../api/client';
import './Header.css';

export default function Header({ onOpenAudit, onOpenUpload }) {
  const { state, dispatch, startRecon } = useReconciliation();
  const { status, progress, language } = state;
  const [profileOpen, setProfileOpen] = useState(false);

  const isRunning = status === 'running';

  const handleRunRecon = async () => {
    if (isRunning) return;
    await startRecon();
  };

  const toggleLanguage = () => {
    dispatch({ type: 'SET_LANGUAGE', language: language === 'en' ? 'hi' : 'en' });
  };

  const getProgressText = () => {
    if (!progress.pass) return 'Initializing Engine...';
    const passNames = ['', 'Exact Match', 'Rule-Based', 'Fuzzy Match', 'AI Diagnostics'];
    return `Pass ${progress.pass} — ${passNames[progress.pass] || ''}: ${progress.total_matched || 0}/${progress.total_records || 100} matched`;
  };

  return (
    <div className="rzp-header-wrapper">
      <header className="rzp-top-header" id="app-header">
        {/* Global Search Bar */}
        <div className="header-search-container">
          <Search size={14} className="search-icon" />
          <input
            id="global-search"
            className="global-search-input"
            placeholder="Search order ID, settlement, amount, flag..."
            value={state.searchQuery || ''}
            onChange={e => dispatch({ type: 'SET_SEARCH_QUERY', query: e.target.value })}
          />
        </div>

        {/* Right Utility Controls */}
        <div className="header-utility-controls">
          {/* Live System Status Badge */}
          <div className="system-status-badge" title="AI Recon Engine Operational Status">
            <span className={`system-status-dot ${isRunning ? 'system-status-dot--busy' : ''}`} />
            <span>{isRunning ? 'Engine Active' : 'System Ready'}</span>
          </div>

          {/* Import CSV Secondary Button */}
          <button
            id="import-csv-btn"
            className="btn btn-secondary header-cta"
            onClick={onOpenUpload}
            title="Import CSV or Excel Batch Report"
          >
            <UploadCloud size={13} />
            <span>Import CSV</span>
          </button>

          {/* Run Recon Primary Button */}
          <button
            id="run-recon-btn"
            className={`btn btn-primary header-cta ${isRunning ? 'btn-running' : ''}`}
            onClick={handleRunRecon}
            disabled={isRunning}
            aria-label="Run Reconciliation"
          >
            {isRunning ? (
              <>
                <RefreshCw size={13} className="animate-spin" />
                Running...
              </>
            ) : (
              <>
                <Play size={13} />
                {status === 'complete' ? 'Re-run Recon' : 'Run Recon'}
              </>
            )}
          </button>

          {/* Profile Dropdown Container */}
          <div className="profile-menu-container">
            <button
              id="profile-avatar-btn"
              className="profile-avatar-btn"
              title="Merchant Settings & Profile"
              aria-label="Merchant Profile"
              onClick={() => setProfileOpen(o => !o)}
            >
              <User size={15} />
              <ChevronDown size={12} />
            </button>

            {profileOpen && (
              <div className="profile-dropdown-menu">
                {/* Merchant Info Header */}
                <div className="profile-menu-header">
                  <div className="merchant-avatar-circle">TC</div>
                  <div className="merchant-info-text">
                    <div className="merchant-name">Trendhive Commerce</div>
                    <div className="merchant-mid font-mono">MID4823099</div>
                  </div>
                </div>

                <div className="profile-menu-divider" />

                {/* Language Toggle Row */}
                <div className="profile-menu-row">
                  <div className="profile-row-left">
                    <Globe size={14} />
                    <span>Language</span>
                  </div>
                  <div
                    id="language-toggle"
                    className="lang-toggle-pill-dropdown"
                    onClick={toggleLanguage}
                    title={language === 'en' ? 'Switch to Hinglish (HI)' : 'Switch to English (EN)'}
                    role="button"
                    tabIndex={0}
                  >
                    <span className={`lang-segment ${language === 'en' ? 'lang-segment--active' : ''}`}>EN</span>
                    <span className={`lang-segment ${language === 'hi' ? 'lang-segment--active' : ''}`}>HI</span>
                  </div>
                </div>

                <div className="profile-menu-divider" />

                {/* Test Mode Row */}
                <div className="profile-menu-row">
                  <div className="profile-row-left">
                    <span className="test-mode-dot" />
                    <span>Test Mode</span>
                  </div>
                  <span className="status-pill-active">Active</span>
                </div>

                <div className="profile-menu-divider" />

                {/* API Docs Button */}
                <button
                  className="profile-menu-row profile-menu-btn"
                  onClick={() => { setProfileOpen(false); window.open(DOCS_URL, '_blank'); }}
                >
                  <div className="profile-row-left">
                    <Code size={14} />
                    <span>API Docs (Swagger)</span>
                  </div>
                </button>
              </div>
            )}
          </div>
        </div>
      </header>
    </div>
  );
}
