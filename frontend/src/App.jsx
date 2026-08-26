import { useState, useRef, useCallback, Component } from 'react';
import './App.css';
import { ReconciliationProvider, useReconciliation } from './context/ReconciliationContext';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import KPIRow from './components/KPIRow';
import ReconWorkbench from './components/ReconWorkbench';
import CashFlowChart from './components/CashFlowChart';
import GatewayBreakdownWidget from './components/GatewayBreakdownWidget';
import CashFlowFullView from './components/CashFlowFullView';
import ReconBreakdownFullView from './components/ReconBreakdownFullView';
import AIExceptionDrawer from './components/AIExceptionDrawer';
import AuditLogPanel from './components/AuditLogPanel';
import CSVImportModal from './components/CSVImportModal';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Dashboard error caught by ErrorBoundary:", error, errorInfo);
  }

  handleReset = () => {
    localStorage.clear();
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          padding: 24,
          textAlign: 'center',
          fontFamily: 'sans-serif',
          background: '#f8fafc',
        }}>
          <h2 style={{ color: '#0c2340', marginBottom: 8, fontSize: 20 }}>RazorRecon UI Recovered</h2>
          <p style={{ color: '#64748b', fontSize: 14, maxWidth: 500, marginBottom: 20 }}>
            {this.state.error?.message || 'An unexpected UI error occurred.'}
          </p>
          <button
            onClick={this.handleReset}
            style={{
              padding: '10px 20px',
              background: '#0b72e7',
              color: '#ffffff',
              border: 'none',
              borderRadius: 6,
              cursor: 'pointer',
              fontWeight: 700,
              fontSize: 13,
            }}
          >
            Clear Cache &amp; Reset Dashboard
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

function MainLayout({
  activeOverlay,
  setActiveOverlay,
  activeView,
  setActiveView,
  sidebarWidth,
  isSidebarCollapsed,
  toggleSidebar,
  isSidebarDragging,
  startSidebarDragging,
  leftWidth,
  isDragging,
  startDragging,
  workbenchRef,
  rightPanelRef,
  rightTopPercentage,
  isRightVerticalDragging,
  startRightVerticalDragging
}) {
  const { state } = useReconciliation();
  const { results = [], status } = state || {};
  const hasData = (results && results.length > 0) || status === 'running';

  return (
    <div className={`rzp-dashboard-layout ${isDragging || isSidebarDragging || isRightVerticalDragging ? 'layout-dragging' : ''}`}>
      {/* Left Sidebar */}
      <Sidebar
        width={sidebarWidth}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={toggleSidebar}
        activeView={activeView}
        onSelectView={setActiveView}
        onOpenAI={() => setActiveOverlay('ai')}
        onOpenAudit={() => setActiveOverlay('audit')}
        onOpenUpload={() => setActiveOverlay('upload')}
      />

      {/* Resizable Sidebar Drag Handle Splitter */}
      <div
        className={`sidebar-resizer ${isSidebarDragging ? 'sidebar-resizer--dragging' : ''}`}
        onMouseDown={startSidebarDragging}
        title="Drag left/right to resize or collapse sidebar"
        role="separator"
        aria-orientation="vertical"
        aria-label="Sidebar Resizer"
      />

      {/* Right Main Body */}
      <div className="rzp-main-wrapper">
        {/* Header */}
        <Header
          onOpenAudit={() => setActiveOverlay('audit')}
          onOpenUpload={() => setActiveOverlay('upload')}
        />

        {/* Main Viewport Body */}
        <main className={`rzp-content-body ${activeView !== 'workbench' ? 'rzp-content-body--fullview' : ''}`} id="main-content">
          {activeView === 'cashflow' ? (
            <CashFlowFullView />
          ) : activeView === 'breakdown' ? (
            <ReconBreakdownFullView />
          ) : (
            <>
              {/* Overview KPI Cards */}
              <KPIRow
                onOpenAI={() => setActiveOverlay('ai')}
                onOpenAudit={() => setActiveOverlay('audit')}
              />

              {/* Workbench Layout: Split panel when data exists; full-width when empty */}
              {hasData ? (
                <div
                  className="app-workbench"
                  ref={workbenchRef}
                  style={{
                    gridTemplateColumns: `${leftWidth}% 8px calc(${100 - leftWidth}% - 8px)`
                  }}
                >
                  {/* Left Panel: Settlements Workbench */}
                  <section className="workbench-left" aria-label="Reconciliation Workbench">
                    <ReconWorkbench onOpenAI={() => setActiveOverlay('ai')} />
                  </section>

                  {/* Drag Handle Splitter Bar */}
                  <div
                    className={`workbench-resizer ${isDragging ? 'workbench-resizer--dragging' : ''}`}
                    onMouseDown={startDragging}
                    title="Click and drag left/right to resize panels"
                    role="separator"
                    aria-orientation="vertical"
                    aria-label="Panel Resizer"
                  />

                  {/* Right Panel: Cash Flow Chart + Gateway Breakdown */}
                  <section className="workbench-right" ref={rightPanelRef} aria-label="Cash Flow Chart & Gateway Breakdown">
                    <div style={{ height: `${rightTopPercentage}%`, minHeight: 0, overflow: 'hidden' }}>
                      <CashFlowChart />
                    </div>

                    <div
                      className={`workbench-vertical-resizer ${isRightVerticalDragging ? 'workbench-vertical-resizer--dragging' : ''}`}
                      onMouseDown={startRightVerticalDragging}
                      title="Click and drag up/down to adjust heights"
                      role="separator"
                      aria-orientation="horizontal"
                      aria-label="Vertical Adjustment Resizer"
                    />

                    <div style={{ height: `calc(${100 - rightTopPercentage}% - 4px)`, minHeight: 0, overflow: 'hidden' }}>
                      <GatewayBreakdownWidget />
                    </div>
                  </section>
                </div>
              ) : (
                <div className="app-workbench" style={{ display: 'block', gridTemplateColumns: 'none' }}>
                  <section className="workbench-left" style={{ width: '100%', height: '100%' }} aria-label="Reconciliation Workbench">
                    <ReconWorkbench onOpenAI={() => setActiveOverlay('ai')} />
                  </section>
                </div>
              )}
            </>
          )}
        </main>
      </div>

      {/* Floating Modal Drawers */}
      <AIExceptionDrawer
        isOpen={activeOverlay === 'ai'}
        onClose={() => setActiveOverlay(null)}
      />

      <AuditLogPanel
        isOpen={activeOverlay === 'audit'}
        onClose={() => setActiveOverlay(null)}
      />

      <CSVImportModal
        isOpen={activeOverlay === 'upload'}
        onClose={() => setActiveOverlay(null)}
      />
    </div>
  );
}

export default function App() {
  const [activeOverlay, setActiveOverlay] = useState(null); // null | 'ai' | 'audit' | 'upload'
  const [activeView, setActiveView] = useState('workbench'); // 'workbench' | 'cashflow' | 'breakdown'

  // Resizable left sidebar state (default 220px)
  const [sidebarWidth, setSidebarWidth] = useState(220);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isSidebarDragging, setIsSidebarDragging] = useState(false);

  // Resizable split pane state
  const [leftWidth, setLeftWidth] = useState(59.5); // initial 59.5% left, 40.5% right
  const [isDragging, setIsDragging] = useState(false);
  const workbenchRef = useRef(null);

  // Vertical resizable right column state
  const [rightTopPercentage, setRightTopPercentage] = useState(46); // initial 46% top chart, 54% bottom breakdown
  const [isRightVerticalDragging, setIsRightVerticalDragging] = useState(false);
  const rightPanelRef = useRef(null);

  // Drag handler for Left Sidebar
  const startSidebarDragging = useCallback((e) => {
    e.preventDefault();
    setIsSidebarDragging(true);

    const onMouseMove = (moveEvent) => {
      const newWidth = moveEvent.clientX;
      if (newWidth < 120) {
        setIsSidebarCollapsed(true);
      } else {
        setIsSidebarCollapsed(false);
        const clamped = Math.min(Math.max(newWidth, 200), 360);
        setSidebarWidth(clamped);
      }
    };

    const onMouseUp = () => {
      setIsSidebarDragging(false);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  }, []);

  // Drag handler for Workbench Horizontal Splitter
  const startDragging = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);

    const onMouseMove = (moveEvent) => {
      if (!workbenchRef.current) return;
      const rect = workbenchRef.current.getBoundingClientRect();
      const offsetX = moveEvent.clientX - rect.left;
      const newPercentage = (offsetX / rect.width) * 100;
      // Clamp between 25% and 75%
      const clamped = Math.min(Math.max(newPercentage, 25), 75);
      setLeftWidth(clamped);
    };

    const onMouseUp = () => {
      setIsDragging(false);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  }, []);

  // Drag handler for Right Column Zero-Space Vertical Splitter
  const startRightVerticalDragging = useCallback((e) => {
    e.preventDefault();
    setIsRightVerticalDragging(true);

    const container = rightPanelRef.current;
    if (!container) return;

    const rect = container.getBoundingClientRect();
    const totalHeight = rect.height;

    const onMouseMove = (moveEvent) => {
      const currentY = moveEvent.clientY - rect.top;
      const percentage = (currentY / totalHeight) * 100;
      const clampedPercentage = Math.max(25, Math.min(75, percentage));
      setRightTopPercentage(clampedPercentage);
    };

    const onMouseUp = () => {
      setIsRightVerticalDragging(false);
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    };

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  }, []);

  const toggleSidebar = () => {
    setIsSidebarCollapsed(prev => !prev);
  };

  return (
    <ErrorBoundary>
      <ReconciliationProvider>
        <MainLayout
          activeOverlay={activeOverlay}
          setActiveOverlay={setActiveOverlay}
          activeView={activeView}
          setActiveView={setActiveView}
          sidebarWidth={sidebarWidth}
          isSidebarCollapsed={isSidebarCollapsed}
          toggleSidebar={toggleSidebar}
          isSidebarDragging={isSidebarDragging}
          startSidebarDragging={startSidebarDragging}
          leftWidth={leftWidth}
          isDragging={isDragging}
          startDragging={startDragging}
          workbenchRef={workbenchRef}
          rightPanelRef={rightPanelRef}
          rightTopPercentage={rightTopPercentage}
          isRightVerticalDragging={isRightVerticalDragging}
          startRightVerticalDragging={startRightVerticalDragging}
        />
      </ReconciliationProvider>
    </ErrorBoundary>
  );
}
