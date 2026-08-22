import { Play, RefreshCw, Activity } from 'lucide-react';
import { useReconciliation } from '../context/ReconciliationContext';
import './Header.css';

export default function Header() {
  const { state, dispatch, startRecon } = useReconciliation();
  const { status, progress, language } = state;

  const isRunning = status === 'running';

  const handleRunRecon = async () => {
    if (isRunning) return;
    await startRecon();
  };

  const toggleLanguage = () => {
    dispatch({ type: 'SET_LANGUAGE', language: language === 'en' ? 'hi' : 'en' });
  };

  const getProgressText = () => {
    if (!progress.pass) return 'Initializing...';
    const passNames = ['', 'Exact Match', 'Rule-Based', 'Fuzzy Match', 'AI Analysis'];
    return `Pass ${progress.pass} — ${passNames[progress.pass] || ''}: ${progress.total_matched || 0}/${progress.total_records || 100} matched`;
  };

  return (
    <header className="header" id="app-header">
      <div className="header-inner">
        {/* Logo + Brand */}
        <div className="header-brand">
          <div className="header-logo" aria-hidden="true">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
              <rect width="32" height="32" rx="6" fill="#2D81E0"/>
              <path d="M8 10h10c2.2 0 4 1.8 4 4s-1.8 4-4 4h-6l5 4" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div>
            <h1 className="header-title">RazorRecon &amp; Flow</h1>
            <p className="header-subtitle">AI Settlement Reconciliation</p>
          </div>
        </div>

        {/* Center: Progress bar (during run) */}
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

        {/* Right: Controls */}
        <div className="header-controls">
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

          {/* Run Recon Button */}
          <button
            id="run-recon-btn"
            className={`btn btn-primary header-cta ${isRunning ? 'btn-running' : ''}`}
            onClick={handleRunRecon}
            disabled={isRunning}
            aria-label="Run Reconciliation"
          >
            {isRunning ? (
              <>
                <RefreshCw size={14} className="animate-spin" />
                Running...
              </>
            ) : (
              <>
                <Play size={14} />
                {status === 'complete' ? 'Re-run Recon' : 'Run Reconciliation'}
              </>
            )}
          </button>
        </div>
      </div>
    </header>
  );
}
