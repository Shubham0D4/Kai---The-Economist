import React, { useState, useEffect } from 'react';
import { Form, InputGroup, Button, Dropdown, DropdownButton, Spinner, Alert } from 'react-bootstrap';
import { Search, Shield, Zap, Scale, Triangle } from 'lucide-react';
import { initiateAnalysis } from '../services/api';
import { useCommittee } from '../context/CommitteeContext';
import { useAuth } from '../context/AuthContext';

const SearchInterface = ({ initialTicker = '' }) => {
    const { addLog, simulateToolCall, setSessionId, setCurrentTicker } = useCommittee();
    const [ticker, setTicker] = useState(initialTicker);
    const [persona, setPersona] = useState('Balanced');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const inputRef = React.useRef(null);

    useEffect(() => {
        if (initialTicker) setTicker(initialTicker);
    }, [initialTicker]);

    // Global Shortcut: Cmd+K / Ctrl+K
    useEffect(() => {
        const handleKeyDown = (e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault();
                inputRef.current?.focus();
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, []);

    const { user } = useAuth();

    const handleAnalysis = async (e) => {
        e.preventDefault();
        if (!ticker) return;

        setLoading(true);
        setError(null);
        setCurrentTicker(ticker);

        try {
            const data = await initiateAnalysis(ticker, persona, user?.username || 'anonymous');
            if (data && data.session_id) {
                setSessionId(data.session_id);
            }
        } catch (err) {
            setError("Failed to initiate analysis. Ensure backend is running.");
            console.error("Analysis error:", err);
        } finally {
            setLoading(false);
        }
    };

    const getPersonaIcon = (p) => {
        switch (p) {
            case 'Zen': return <Shield size={18} className="text-success" />;
            case 'Alpha': return <Zap size={18} className="text-danger" />;
            default: return <Scale size={18} className="text-primary" />;
        }
    };

    return (
        <div className="glass-panel p-5 shadow-lg animate-fade-in-up" style={{ maxWidth: '750px', margin: '6rem auto 4rem auto' }}>
            <div className="text-center mb-5">
                <h1 className="fw-bolder mb-3 display-5 ls-tight">
                    <span className="text-gradient">Market Intelligence</span>
                </h1>
                <p className="text-secondary fs-5 opacity-75" style={{ maxWidth: '500px', margin: '0 auto' }}>
                    Deploy an autonomous council of AI agents to analyze any ticker with institutional depth.
                </p>
            </div>

            <Form onSubmit={handleAnalysis}>
                <div className="position-relative mb-5 mx-auto" style={{ maxWidth: '600px' }}>
                    <Form.Control
                        ref={inputRef}
                        size="lg"
                        placeholder="Enter Ticker (Cmd + K)"
                        className="py-3 px-5 rounded-pill fs-4 shadow-sm"
                        style={{ paddingLeft: '60px', height: '64px', backgroundColor: 'var(--bg-surface)', color: 'var(--text-primary)', border: '1px solid var(--border)' }}
                        value={ticker}
                        onChange={(e) => setTicker(e.target.value.toUpperCase())}
                    />
                    <Search className="position-absolute opacity-50" size={26} style={{ left: '24px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
                </div>

                <div className="d-flex gap-3 justify-content-center mb-5">
                    {['Zen', 'Balanced', 'Alpha'].map((p) => (
                        <div
                            key={p}
                            onClick={() => setPersona(p)}
                            className={`px-4 py-2 rounded-pill cursor-pointer d-flex align-items-center gap-2 transition-all user-select-none ${persona === p ? 'bg-primary text-white shadow-md scale-up' : 'bg-white bg-opacity-50 text-muted border border-light hover-bg-white'}`}
                            style={{ cursor: 'pointer', transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)' }}
                        >
                            {getPersonaIcon(p)}
                            <span className="fw-medium">{p}</span>
                        </div>
                    ))}
                </div>

                <div className="d-grid justify-content-center">
                    <Button
                        variant="primary"
                        size="lg"
                        type="submit"
                        disabled={loading}
                        className="rounded-pill py-3 px-5 fw-bold fs-5 shadow-lg position-relative overflow-hidden btn-glow"
                        style={{ minWidth: '250px' }}
                    >
                        {loading ? (
                            <div className="d-flex align-items-center justify-content-center gap-2">
                                <Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" />
                                <span>Coordinating Agents...</span>
                            </div>
                        ) : (
                            'Initiate Debate'
                        )}
                    </Button>
                </div>
            </Form>

            {error && <Alert variant="danger" className="mt-4 text-center rounded-3 border-0 bg-danger-subtle text-danger mx-auto" style={{ maxWidth: '500px' }}>{error}</Alert>}

            <div className="text-center mt-5">
                <small className="text-muted opacity-50 ls-1 text-uppercase fw-bold" style={{ fontSize: '0.7rem' }}>
                    Powered by Kai-Consensus Protocol 2.0
                </small>
            </div>
        </div>
    );
};

export default SearchInterface;
