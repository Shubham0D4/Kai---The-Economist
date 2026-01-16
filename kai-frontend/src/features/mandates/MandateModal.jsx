import React, { useState } from 'react';
import { Modal, Button, Alert } from 'react-bootstrap';
import { ShieldAlert, CheckCircle, XCircle, Fingerprint } from 'lucide-react';
import { approveMandate, rejectMandate } from '../../services/api';
import { useCommittee } from '../../context/CommitteeContext';

const MandateModal = () => {
    const { mandateRequest, setMandateRequest, addLog } = useCommittee();
    const [processing, setProcessing] = useState(false);

    if (!mandateRequest) return null;

    const { id, action, details, riskLevel, sessionId, challengeId } = mandateRequest;

    const handleDecision = async (decision) => {
        setProcessing(true);
        try {
            if (decision === 'approve') {
                addLog({
                    timestamp: new Date().toISOString(),
                    agent: 'User',
                    message: `Signed Mandate #${id} for: ${action}`
                });
                // Call API if sessionId exists (real mode)
                if (sessionId && challengeId) {
                    await approveMandate(sessionId, challengeId);
                }
            } else {
                addLog({
                    timestamp: new Date().toISOString(),
                    agent: 'User',
                    message: `Rejected Mandate #${id}`
                });
                // Call API if sessionId exists (real mode)
                if (sessionId) {
                    await rejectMandate(sessionId);
                }
            }

            // Simulating API delay for demo smoothness regardless of real/mock
            await new Promise(resolve => setTimeout(resolve, 800));

            setMandateRequest(null); // Close modal
        } catch (error) {
            console.error("Mandate error:", error);
        } finally {
            setProcessing(false);
        }
    };

    return (
        <Modal show={!!mandateRequest} onHide={() => handleDecision('reject')} centered backdrop="static" keyboard={false}>
            <Modal.Header className="bg-warning-subtle text-dark border-bottom-0">
                <Modal.Title className="d-flex align-items-center gap-2 fw-bold">
                    <ShieldAlert className="text-warning-emphasis" />
                    Approval Required (HITL)
                </Modal.Title>
            </Modal.Header>

            <Modal.Body className="p-4">
                <Alert variant="secondary" className="mb-4 text-center">
                    <Fingerprint size={24} className="mb-2 text-dark" />
                    <div className="fw-semibold">AP2 Secure Signature Request</div>
                    <small className="font-monospace text-muted">{id}</small>
                </Alert>

                <h5 className="fw-bold mb-2">{action}</h5>
                <p className="text-secondary">{details}</p>

                {riskLevel === 'HIGH' && (
                    <Alert variant="danger">
                        <strong>Warning:</strong> This action exceeds standard risk thresholds.
                    </Alert>
                )}
            </Modal.Body>

            <Modal.Footer className="border-top-0 d-flex justify-content-between p-4 bg-light rounded-bottom">
                <Button variant="outline-danger" onClick={() => handleDecision('reject')} disabled={processing} className="d-flex align-items-center gap-2 px-4">
                    <XCircle size={18} /> Reject
                </Button>
                <Button variant="success" onClick={() => handleDecision('approve')} disabled={processing} className="d-flex align-items-center gap-2 px-4 fw-bold shadow-sm">
                    {processing ? 'Signing...' : (
                        <>
                            <CheckCircle size={18} /> Approve & Sign
                        </>
                    )}
                </Button>
            </Modal.Footer>
        </Modal>
    );
};

export default MandateModal;
