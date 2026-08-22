import { useState, useRef, useCallback } from 'react';
import './App.css';
import { ReconciliationProvider } from './context/ReconciliationContext';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import KPIRow from './components/KPIRow';
import ReconWorkbench from './components/ReconWorkbench';
import CashFlowChart from './components/CashFlowChart';
import AIExceptionDrawer from './components/AIExceptionDrawer';
import AuditLogPanel from './components/AuditLogPanel';

export default function App() {
  const [activeOverlay, setActiveOverlay] = useState(null); // null | 'ai' | 'audit'

  // Resizable left sidebar state
  const [sidebarWidth, setSidebarWidth] = useState(220);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isSidebarDragging, setIsSidebarDragging] = useState(false);

  // Resizable split pane state
  const [leftWidth, setLeftWidth] = useState(58); // initial 58% left, 42% right
  const [isDragging, setIsDragging] = useState(false);
  const workbenchRef = useRef(null);

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
        const clamped = Math.min(Math.max(newWidth, 180), 360);
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

  // Drag handler for Workbench Splitter
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

  const toggleSidebar = () => {
    setIsSidebarCollapsed(prev => !prev);
  };

  return (
    <ReconciliationProvider>
      <div className={`rzp-dashboard-layout ${isDragging || isSidebarDragging ? 'layout-dragging' : ''}`}>
        {/* Left Sidebar */}
        <Sidebar
          width={sidebarWidth}
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={toggleSidebar}
          onOpenAI={() => setActiveOverlay('ai')}
          onOpenAudit={() => setActiveOverlay('audit')}
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
          />

          {/* Main Single-Viewport Body */}
          <main className="rzp-content-body" id="main-content">
            {/* Overview KPI Cards + Links Bar */}
            <KPIRow
              onOpenAI={() => setActiveOverlay('ai')}
              onOpenAudit={() => setActiveOverlay('audit')}
            />

            {/* Split Workbench Layout (Resizable Settlements Table + 7-Day Cash Flow) */}
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

              {/* Right Panel: Cash Flow Chart */}
              <section className="workbench-right" aria-label="Cash Flow Chart">
                <CashFlowChart />
              </section>
            </div>
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
      </div>
    </ReconciliationProvider>
  );
}
