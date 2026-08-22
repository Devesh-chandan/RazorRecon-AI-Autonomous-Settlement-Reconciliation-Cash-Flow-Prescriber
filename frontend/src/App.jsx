import './App.css';
import { ReconciliationProvider } from './context/ReconciliationContext';
import Header from './components/Header';
import KPIRow from './components/KPIRow';
import ReconWorkbench from './components/ReconWorkbench';
import CashFlowChart from './components/CashFlowChart';
import AIExceptionDrawer from './components/AIExceptionDrawer';
import AuditLogPanel from './components/AuditLogPanel';

export default function App() {
  return (
    <ReconciliationProvider>
      <div className="app-shell">
        {/* Sticky header */}
        <Header />

        {/* Main scrollable content */}
        <main className="app-main" id="main-content">
          {/* KPI Row */}
          <KPIRow />

          {/* Split Workbench Layout */}
          <div className="app-workbench">
            {/* Left: Recon Table (55%) */}
            <section className="workbench-left" aria-label="Reconciliation Workbench">
              <ReconWorkbench />
            </section>

            {/* Right: Cash Flow Chart (45%) */}
            <section className="workbench-right" aria-label="Cash Flow Chart">
              <CashFlowChart />
            </section>
          </div>
        </main>

        {/* Bottom: AI Exception Drawer (slide-up) */}
        <AIExceptionDrawer />

        {/* Audit Log */}
        <AuditLogPanel />
      </div>
    </ReconciliationProvider>
  );
}
