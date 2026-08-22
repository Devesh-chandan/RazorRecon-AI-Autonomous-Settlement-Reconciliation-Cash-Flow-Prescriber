import { Play, RefreshCw, Activity, Search, User, ChevronDown } from 'lucide-react';
import { useReconciliation } from '../context/ReconciliationContext';
import './Header.css';

export default function Header({ onOpenAudit }) {
  const { state, dispatch, startRecon } = useReconciliation();
  const { status, progress, language, results } = state;

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
            placeholder="Search order ID, settlement, flag..."
          />
        </div>

        {/* Live Progress Bar (During Run) */}
        {isRunning && (
          <div className="header-progress" aria-live="polite">
            <div className="header-progress-bar">
              <div
                className="header-progress-fill"
                style={{
                  width: progress.total_records
                    ? `${((progress.total_matched || 0) / progress.total_records) * 100}%`
                    : '10%',
                }}
              />
            </div>
            <span className="header-progress-text">
              <Activity size={12} className="animate-spin" />
              {getProgressText()}
            </span>
          </div>
        )}

        {/* Right Utility Controls */}
        <div className="header-utility-controls">
          {/* Live System Status Badge */}
          <div className="system-status-badge" title="AI Recon Engine Operational Status">
            <span className={`system-status-dot ${isRunning ? 'system-status-dot--busy' : ''}`} />
            <span>{isRunning ? 'Engine Active' : 'System Ready'}</span>
          </div>

          {/* Test Mode Badge Toggle */}
          <div className="test-mode-badge" title="AI Multi-Pass Engine Active in Test Mode">
            <span className="test-mode-dot" />
            <span>Test Mode</span>
            <ChevronDown size={12} className="text-tertiary" />
          </div>



          {/* API Docs Button */}
          <button
            className="icon-btn user-avatar-btn"
            title="API Documentation (Swagger)"
            aria-label="API Documentation"
            onClick={() => window.open('http://localhost:8000/docs', '_blank')}
          >
            <User size={15} />
          </button>

          {/* Language Toggle */}
          <button
            id="language-toggle"
            className={`lang-toggle ${language === 'hi' ? 'lang-toggle--active' : ''}`}
            onClick={toggleLanguage}
            title={language === 'en' ? 'Switch to Hinglish' : 'Switch to English'}
            aria-label="Toggle language"
          >
            <span className={`lang-option ${language === 'en' ? 'active' : ''}`}>EN</span>
            <span className="lang-divider">|</span>
            <span className={`lang-option ${language === 'hi' ? 'active' : ''}`}>HI</span>
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
        </div>
      </header>
    </div>
  );
}
