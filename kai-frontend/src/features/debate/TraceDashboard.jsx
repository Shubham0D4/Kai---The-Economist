import React from 'react';
import { Accordion, Table, Badge } from 'react-bootstrap';
import { Activity, Clock, Coins, Server } from 'lucide-react';
import { useCommittee } from '../../context/CommitteeContext';

const TraceDashboard = () => {
    const { traceLogs } = useCommittee();

    return (
        <div className="mt-5 mb-5">
            <Accordion>
                <Accordion.Item eventKey="0" className="border shadow-sm">
                    <Accordion.Header>
                        <div className="d-flex align-items-center gap-2 text-muted fw-bold">
                            <Activity size={18} />
                            Technical Trace (Observability)
                            <Badge bg="light" text="dark" className="border ms-2">
                                {traceLogs.length} Events
                            </Badge>
                        </div>
                    </Accordion.Header>
                    <Accordion.Body className="p-0">
                        <div className="table-responsive" style={{ maxHeight: '300px' }}>
                            <Table striped hover borderless className="mb-0 align-middle">
                                <thead className="bg-light sticky-top">
                                    <tr>
                                        <th className="small text-uppercase text-muted ps-4">Timestamp</th>
                                        <th className="small text-uppercase text-muted">Agent</th>
                                        <th className="small text-uppercase text-muted">Step / Tool</th>
                                        <th className="small text-uppercase text-muted text-end">Latency</th>
                                        <th className="small text-uppercase text-muted text-end">Tokens</th>
                                        <th className="small text-uppercase text-muted text-center pe-4">Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {traceLogs.length === 0 ? (
                                        <tr>
                                            <td colSpan="6" className="text-center py-4 text-muted small">
                                                No trace data available. Start a debate to see telemetry.
                                            </td>
                                        </tr>
                                    ) : (
                                        traceLogs.map((trace) => (
                                            <tr key={trace.id}>
                                                <td className="ps-4 small font-monospace text-secondary">
                                                    {new Date(trace.timestamp).toISOString().split('T')[1].slice(0, -1)}
                                                </td>
                                                <td>
                                                    <Badge bg="light" text="dark" className="border">{trace.agent}</Badge>
                                                </td>
                                                <td className="small fw-semibold text-primary">
                                                    {trace.step}
                                                </td>
                                                <td className="text-end small font-monospace">
                                                    <span className={`${trace.latency > 500 ? 'text-warning' : 'text-success'}`}>
                                                        {trace.latency}ms
                                                    </span>
                                                </td>
                                                <td className="text-end small font-monospace text-muted">
                                                    {trace.tokens}
                                                </td>
                                                <td className="text-center pe-4">
                                                    <Badge bg={trace.status === 'SUCCESS' ? 'success' : 'danger'} style={{ fontSize: '0.6em' }}>
                                                        {trace.status}
                                                    </Badge>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </Table>
                        </div>
                    </Accordion.Body>
                </Accordion.Item>
            </Accordion>
        </div>
    );
};

export default TraceDashboard;
