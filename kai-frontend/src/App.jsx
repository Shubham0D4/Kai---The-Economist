import React, { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { CommitteeProvider, useCommittee } from './context/CommitteeContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import ToolCallIndicator from './components/ToolCallIndicator';
import SearchInterface from './components/SearchInterface';
import DebateFeed from './features/debate/DebateFeed';
import SigmaCard from './features/debate/SigmaCard';
import MandateModal from './features/mandates/MandateModal';
import TraceDashboard from './features/debate/TraceDashboard';
import Login from './features/auth/Login';
import Register from './features/auth/Register';
import AgentStatusGrid from './features/debate/AgentStatusGrid';
import Dashboard from './pages/Dashboard';
import TickerPage from './pages/TickerPage';
import ChatWidget from './components/ChatWidget';

// Protected Route Wrapper
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return <div className="p-5 text-center">Loading session...</div>;
  return isAuthenticated ? children : <Navigate to="/login" />;
};

import { Moon, Sun } from 'lucide-react';

function AppContent() {
  const { user, logout } = useAuth();
  const { simulateToolCall, setFinalReport, setMandateRequest, currentTicker } = useCommittee();

  // Theme State
  const [theme, setTheme] = useState(localStorage.getItem('kai_theme') || 'light');

  React.useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('kai_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  const handleSimulateDecision = () => {
    const signals = ['BUY', 'HOLD', 'SELL'];
    const randomSignal = signals[Math.floor(Math.random() * signals.length)];
    const confidence = Math.floor(Math.random() * 30) + 65; // 65-95

    setFinalReport({
      ticker: currentTicker,
      signal: randomSignal,
      confidence: confidence,
      scores: {
        faithfulness: Math.floor(Math.random() * 15) + 80,
        consistency: Math.floor(Math.random() * 15) + 80
      },
      summary: `Real-time analysis for ${currentTicker} shows a ${randomSignal} signal with ${confidence}% confidence. Our council of agents identified key drivers in both fundamental data and recent market sentiment traces.`
    });
  };

  const handleSimulateMandate = () => {
    const isHigh = Math.random() > 0.5;
    setMandateRequest({
      id: 'AP2-' + Math.floor(Math.random() * 10000),
      action: `Execute ${Math.random() > 0.5 ? 'BUY' : 'SELL'} Order: ${Math.floor(Math.random() * 100) + 10} Shares ${currentTicker}`,
      details: `Sigma Agent has detected a high-conviction pattern for ${currentTicker}. This transaction requires manual validation due to ${isHigh ? 'significant portfolio exposure (>5%)' : 'unusual volatility detected in recent news streams'}.`,
      riskLevel: isHigh ? 'HIGH' : 'MEDIUM'
    });
  };

  return (
    <div className="container py-4">
      <header className="d-flex justify-content-between align-items-center mb-5 pb-3">
        <div className="d-flex align-items-center gap-3">
          <div className="d-flex align-items-center justify-content-center bg-primary bg-gradient text-white rounded-circle" style={{ width: '40px', height: '40px' }}>
            K
          </div>
          <div>
            <h3 className="mb-0 fw-bold text-gradient">Kai Economist</h3>
            <small className="text-muted" style={{ fontSize: '0.8rem' }}>Explainable Investing Copilot</small>
          </div>
        </div>

        <div className="d-flex align-items-center gap-3">
          <button
            onClick={toggleTheme}
            className="btn btn-sm btn-link text-decoration-none d-flex align-items-center justify-content-center nav-link transition-all"
            style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'var(--bg-2)' }}
          >
            {theme === 'light' ? <Moon size={18} className="text-dark" /> : <Sun size={18} className="text-warning" />}
          </button>

          {user && (
            <div className="d-flex align-items-center gap-3 glass-panel px-3 py-2 rounded-pill">
              <span className="small text-muted">User: <strong className="text-primary">{user.username}</strong></span>
              <button onClick={logout} className="btn btn-sm btn-outline-danger px-3 rounded-pill border-0 bg-transparent">Logout</button>
            </div>
          )}
        </div>
      </header>

      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/" element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        } />
        <Route path="/ticker/:symbol" element={
          <ProtectedRoute>
            <TickerPage />
          </ProtectedRoute>
        } />
      </Routes>

      {/* Dev Tools Panel - Only show when logged in */}
      {user && (
        <div className="fixed-bottom p-4 glass-panel border-top d-flex gap-3 justify-content-center m-4 rounded-4 shadow-lg" style={{ maxWidth: '800px', left: '0', right: '0', margin: '0 auto 30px auto', zIndex: 1000, backgroundColor: 'var(--bg-surface)' }}>
          <div className="d-flex align-items-center border-end pe-4 me-2">
            <span className="badge bg-dark text-white p-2">DEV MODE</span>
          </div>
          <button className="btn btn-outline-primary fw-bold" onClick={() => simulateToolCall('charlie', 'fetch_sec_filing')}>
            Simulate Tool Call
          </button>
          <button className="btn btn-success fw-bold text-white shadow-sm" onClick={handleSimulateDecision}>
            Simulate Decision
          </button>
          <button className="btn btn-warning fw-bold text-dark shadow-sm" onClick={handleSimulateMandate}>
            Trigger HITL Mandate
          </button>
        </div>
      )}

      <p className="text-center mt-5 mb-5 text-muted small opacity-50">
        Kai - Explainable Investing Copilot &copy; 2024
      </p>
      <ToolCallIndicator />
      <MandateModal />
      <ChatWidget />
    </div>
  )
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <CommitteeProvider>
          <AppContent />
        </CommitteeProvider>
      </AuthProvider>
    </Router>
  )
}

export default App
