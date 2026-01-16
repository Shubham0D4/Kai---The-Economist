import React, { createContext, useContext, useState, useEffect } from 'react';
import { getSessionLogs, getAnalysisStatus } from '../services/api';

// Context for the Committee (Agents + Debate State)
const CommitteeContext = createContext();

export const useCommittee = () => useContext(CommitteeContext);

export const CommitteeProvider = ({ children }) => {
    // State for active agents in the session
    const [activeAgents, setActiveAgents] = useState({
        charlie: { name: 'Charlie', role: 'Fundamental', status: 'idle' },
        delta: { name: 'Delta', role: 'Sentiment', status: 'idle' },
        gamma: { name: 'Gamma', role: 'Valuation', status: 'idle' },
        sigma: { name: 'Sigma', role: 'Judge', status: 'idle' }
    });

    // State for the currently active tool call (for visualization)
    const [activeToolCall, setActiveToolCall] = useState(null);
    // Example: { agent: 'charlie', tool: 'fetch_filing_data', status: 'running' }

    // State for debate logs/messages
    const [debateLogs, setDebateLogs] = useState([]);

    // State for Active Session
    const [sessionId, setSessionId] = useState(null);
    const [currentTicker, setCurrentTicker] = useState('AAPL'); // Default fallback

    // State for the final Sigma Decision Report
    const [finalReport, setFinalReport] = useState(null);

    // State for Agent Protocol Mandate Requests (HITL)
    const [mandateRequest, setMandateRequest] = useState(null);

    // State for Technical Traces (Observability)
    const [traceLogs, setTraceLogs] = useState([]);

    // Polling effect for logs
    useEffect(() => {
        let interval;
        let retryCount = 0;
        const MAX_RETRIES = 5;

        if (sessionId) {
            const fetchLogs = async () => {
                try {
                    const logs = await getSessionLogs(sessionId);
                    retryCount = 0; // Reset on success

                    if (logs && logs.length > 0) {
                        setDebateLogs(logs);

                        // Derive active status from latest logs
                        const latestLog = logs[logs.length - 1];
                        const newAgents = { ...activeAgents };
                        Object.keys(newAgents).forEach(k => newAgents[k].status = 'idle');
                        let currentTool = null;

                        if (latestLog.agent === 'system') {
                            const msg = latestLog.message.toLowerCase();
                            if (msg.includes('charlie')) {
                                newAgents.charlie.status = 'thinking';
                                currentTool = { agent: 'charlie', tool: 'SEC Filing Analysis', status: 'running' };
                            } else if (msg.includes('delta')) {
                                newAgents.delta.status = 'thinking';
                                currentTool = { agent: 'delta', tool: 'Sentiment Analysis', status: 'running' };
                            } else if (msg.includes('gamma')) {
                                newAgents.gamma.status = 'thinking';
                                currentTool = { agent: 'gamma', tool: 'Valuation Math', status: 'running' };
                            } else if (msg.includes('sigma')) {
                                newAgents.sigma.status = 'thinking';
                            }
                        }

                        setActiveAgents(newAgents);
                        setActiveToolCall(currentTool);
                    }

                    // Also poll status to check for completion and alpha packet
                    const statusData = await getAnalysisStatus(sessionId);
                    if (statusData && statusData.ticker) {
                        setCurrentTicker(statusData.ticker);
                    }

                    if (statusData && statusData.status === 'COMPLETED' && statusData.alpha_packet) {
                        const ap = statusData.alpha_packet;
                        setFinalReport({
                            ticker: statusData.ticker,
                            signal: ap.recommendation,
                            confidence: ap.confidence,
                            summary: ap.debate_summary?.consensus || "Analysis complete.",
                            scores: {
                                faithfulness: ap.quality_scores?.faithfulness || 0,
                                consistency: ap.quality_scores?.consistency || 0
                            }
                        });

                        // Stop polling once completed
                        if (interval) clearInterval(interval);
                    }
                } catch (error) {
                    console.error("Polling error:", error);

                    if (error.response && error.response.status === 401) {
                        console.error("Authentication lost during polling. Stopping.");
                        if (interval) clearInterval(interval);
                        return;
                    }

                    retryCount++;
                    if (retryCount >= MAX_RETRIES) {
                        console.warn("Max polling retries reached. Context may be stale.");
                        if (interval) clearInterval(interval);
                    }
                }
            };

            fetchLogs();
            interval = setInterval(fetchLogs, 4000); // Poll every 4 seconds for reliability
        }

        return () => {
            if (interval) clearInterval(interval);
        };
    }, [sessionId]);

    // Mock function to simulate receiving a tool call event (in real app, this comes from WebSocket/SSE)
    const simulateToolCall = (agent, toolName) => {
        setActiveToolCall({ agent, tool: toolName, status: 'running' });

        // Auto-clear after random duration to simulate completion
        setTimeout(() => {
            setActiveToolCall(null);

            // Add a trace log for this completed action
            const latency = Math.floor(Math.random() * 800) + 200; // 200-1000ms
            const tokens = Math.floor(Math.random() * 500) + 50; // 50-550 tokens

            setTraceLogs(prev => [...prev, {
                id: 'TRC-' + Math.floor(Math.random() * 100000),
                timestamp: new Date().toISOString(),
                agent: agent,
                step: toolName,
                latency: latency,
                tokens: tokens,
                status: 'SUCCESS'
            }]);

        }, 2500);
    };

    const addLog = (log) => {
        setDebateLogs(prev => [...prev, log]);
    };

    const value = {
        activeAgents,
        activeToolCall,
        sessionId,
        setSessionId,
        debateLogs,
        finalReport,
        setFinalReport,
        mandateRequest,
        setMandateRequest,
        traceLogs,
        currentTicker,
        setCurrentTicker,
        simulateToolCall, // Exposed for testing/demo
        addLog
    };

    return (
        <CommitteeContext.Provider value={value}>
            {children}
        </CommitteeContext.Provider>
    );
};
