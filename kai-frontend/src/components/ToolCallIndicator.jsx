import React from 'react';
import { useCommittee } from '../context/CommitteeContext';
import { Terminal, Bot, Server, Loader2 } from 'lucide-react';
import { Badge } from 'react-bootstrap';
import '../styles/tool-indicator.scss'; // We'll create this next

const ToolCallIndicator = () => {
    const { activeToolCall } = useCommittee();

    if (!activeToolCall) return null;

    const getAgentColor = (agent) => {
        switch (agent?.toLowerCase()) {
            case 'charlie': return 'primary';
            case 'delta': return 'warning'; // Orange-ish
            case 'gamma': return 'success';
            case 'sigma': return 'danger';
            default: return 'secondary';
        }
    };

    return (
        <div className="tool-call-indicator-container">
            <div className={`tool-pill shadow-lg border border-${getAgentColor(activeToolCall.agent)}`}>
                <div className="d-flex align-items-center gap-2">
                    {/* Icon based on tool type (simplified logic) */}
                    <Bot size={18} className={`text-${getAgentColor(activeToolCall.agent)}`} />

                    <div className="d-flex flex-column">
                        <span className="small fw-bold text-uppercase text-muted" style={{ fontSize: '0.65rem' }}>
                            {activeToolCall.agent}
                        </span>
                        <span className="fw-semibold d-flex align-items-center gap-2">
                            {activeToolCall.tool}
                            <Loader2 size={12} className="spin-animation" />
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ToolCallIndicator;
