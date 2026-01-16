import React from 'react';
import { Card, Badge, Spinner } from 'react-bootstrap';
import { useCommittee } from '../../context/CommitteeContext';
import { User, Activity, Code, Cpu } from 'lucide-react';

const AgentStatusGrid = () => {
    const { activeAgents } = useCommittee();

    const getAgentIcon = (id) => {
        switch (id) {
            case 'charlie': return <User size={20} />;
            case 'delta': return <Activity size={20} />;
            case 'gamma': return <Code size={20} />;
            case 'sigma': return <Cpu size={20} />;
            default: return <User size={20} />;
        }
    };

    return (
        <div className="agent-status-grid mb-4">
            <h5 className="text-muted small fw-bold text-uppercase mb-3 tracking-wider">
                Active Committee Members
            </h5>
            <div className="row g-4">
                {Object.entries(activeAgents).map(([id, agent]) => (
                    <div key={id} className="col-md-3">
                        <Card className={`h-100 border-0 shadow-sm rounded-4 transition-all ${agent.status === 'thinking' ? 'agent-card-active' : 'agent-card-idle'}`}>
                            <Card.Body className="p-3 d-flex align-items-center gap-3">
                                <div className={`agent-icon-wrapper rounded-circle p-2 ${agent.status === 'thinking' ? 'bg-primary text-white scale-up' : 'bg-light text-muted'}`}>
                                    {getAgentIcon(id)}
                                </div>
                                <div className="flex-grow-1 overflow-hidden">
                                    <div className="d-flex justify-content-between align-items-start">
                                        <h6 className="mb-0 fw-bold text-truncate">{agent.name}</h6>
                                        {agent.status === 'thinking' && (
                                            <Spinner animation="grow" size="sm" variant="primary" className="ms-auto" />
                                        )}
                                    </div>
                                    <p className="text-muted small mb-0">{agent.role}</p>
                                </div>
                            </Card.Body>
                        </Card>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default AgentStatusGrid;
