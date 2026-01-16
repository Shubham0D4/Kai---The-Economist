import React from 'react';
import { OverlayTrigger, Popover, Badge } from 'react-bootstrap';
import { Database } from 'lucide-react';

const CitationPopover = ({ sourceId }) => {
    // In a real app, this would fetch the specific chunk from the backend/context using sourceId
    const mockSourceData = {
        title: `Source Artifact #${sourceId}`,
        content: "This is a raw data chunk retrieved from the Semantic Cache. It represents the grounded truth used by the agent.",
        confidence: "98.5%"
    };

    const popover = (
        <Popover id={`popover-citation-${sourceId}`} className="shadow-lg">
            <Popover.Header as="h3" className="d-flex align-items-center gap-2 bg-light">
                <Database size={16} className="text-primary" />
                <span className="fw-bold">{mockSourceData.title}</span>
            </Popover.Header>
            <Popover.Body>
                <p className="mb-2 small text-muted font-monospace border p-2 rounded bg-white">
                    {mockSourceData.content}
                </p>
                <div className="d-flex justify-content-between align-items-center">
                    <small className="text-success fw-bold">Confidence: {mockSourceData.confidence}</small>
                    <Badge bg="secondary" style={{ fontSize: '0.6em' }}>MCP-001</Badge>
                </div>
            </Popover.Body>
        </Popover>
    );

    return (
        <OverlayTrigger trigger="click" placement="top" overlay={popover} rootClose>
            <Badge
                bg="light"
                text="dark"
                className="ms-1 border cursor-pointer citation-badge text-decoration-none"
                style={{ cursor: 'pointer', transition: 'all 0.2s' }}
                title="Click to verify source"
            >
                [{sourceId}]
            </Badge>
        </OverlayTrigger>
    );
};

export default CitationPopover;
