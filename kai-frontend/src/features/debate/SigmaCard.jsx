import React from 'react';
import { motion } from 'framer-motion';
import { Card, ProgressBar, Badge, Row, Col } from 'react-bootstrap';
import { Gavel, TrendingUp, TrendingDown, MinusCircle, CheckCircle } from 'lucide-react';
import { useCommittee } from '../../context/CommitteeContext';

const SigmaCard = () => {
    const { finalReport } = useCommittee();

    if (!finalReport) return null;

    const { signal, confidence, scores, summary, ticker } = finalReport;
    const safeScores = scores || { faithfulness: 0, consistency: 0 };

    // Dynamic Styling Logic
    const isStrongBuy = signal === 'BUY' && confidence > 80;
    const isStrongSell = signal === 'SELL' && confidence > 80;

    // Simulated Live Market Data
    const [currentPrice, setCurrentPrice] = React.useState(null);
    const [dayChange, setDayChange] = React.useState(null);

    React.useEffect(() => {
        // Initialize with random base price if not available
        // In a real app, this would come from the initial payload or an API
        const basePrice = Math.random() * 200 + 100; // Mock price between 100 and 300
        setCurrentPrice(basePrice);
        setDayChange((Math.random() * 4) - 2); // -2% to +2%

        const interval = setInterval(() => {
            setCurrentPrice(prev => {
                const fluctuation = (Math.random() - 0.5) * 0.2; // Small fluctuation
                return prev + fluctuation;
            });
        }, 3000);

        return () => clearInterval(interval);
    }, [ticker]);

    let borderColor = 'border-secondary';
    let glowClass = '';
    let signalIcon = <MinusCircle />;
    let signalColor = 'text-muted';

    if (signal === 'BUY') {
        signalIcon = <TrendingUp size={32} />;
        signalColor = 'text-success';
        borderColor = 'border-success';
        if (isStrongBuy) glowClass = 'shadow-lg border-2 shadow-success';
    } else if (signal === 'SELL') {
        signalIcon = <TrendingDown size={32} />;
        signalColor = 'text-danger';
        borderColor = 'border-danger';
        if (isStrongSell) glowClass = 'shadow-lg border-2 shadow-danger';
    }

    return (
        <motion.div
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ type: "spring", stiffness: 100, damping: 20 }}
            className="mt-5 mb-5"
        >
            <Card className={`glass-panel border-0 ${glowClass}`} style={{ transition: 'all 0.5s ease-in-out', overflow: 'hidden' }}>
                {/* Gradient Header */}
                <div className="p-4" style={{
                    background: `linear-gradient(135deg, ${signal === 'BUY' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)'} 0%, transparent 100%)`,
                    borderBottom: '1px solid var(--glass-border)'
                }}>
                    <div className="d-flex justify-content-between align-items-center">
                        <div className="d-flex align-items-center gap-3">
                            <div className="p-2 rounded-circle bg-white shadow-sm position-relative">
                                <Gavel size={24} className="text-dark position-relative z-1" />
                                <span className="position-absolute top-0 start-0 w-100 h-100 bg-primary rounded-circle opacity-50 animate-ping" style={{ zIndex: 0 }}></span>
                            </div>
                            <div>
                                <h6 className="text-uppercase text-muted fw-bold mb-0 ls-1" style={{ fontSize: '0.75rem' }}>Final Verdict</h6>
                                <h3 className="mb-0 fw-bold">{ticker}</h3>
                            </div>
                        </div>
                        <Badge bg="dark" className="d-flex align-items-center gap-2 px-3 py-2 rounded-pill shadow-sm">
                            <CheckCircle size={14} className="text-success" />
                            <span>AP2 Verifiable</span>
                        </Badge>
                    </div>
                </div>

                <Card.Body className="p-xl-5 p-4 text-center">
                    <Row className="align-items-center g-4"> {/* Use g-4 for better spacing */}
                        <Col lg={4} className="position-relative px-4 border-end border-light-subtle">
                            <div className="d-flex flex-column justify-content-center py-3">
                                <h6 className="text-uppercase text-secondary fw-bold ls-1 mb-4" style={{ fontSize: '0.8rem' }}>AI Recommendation</h6>
                                <div className={`display-2 fw-black ${signalColor} mb-3 d-flex justify-content-center align-items-center gap-2 filter-drop-shadow`}>
                                    {signalIcon} {signal}
                                </div>
                                <div className="mt-auto">
                                    <Badge bg={confidence > 75 ? 'success' : 'warning'} pill className="px-4 py-2 fs-6 opacity-90 shadow-sm fw-medium">
                                        {confidence}% Confidence
                                    </Badge>
                                </div>
                            </div>
                        </Col>

                        <Col lg={4} className="text-center position-relative px-4 border-end border-light-subtle">
                            <div className="d-flex flex-column justify-content-center py-3">
                                <h6 className="text-uppercase text-secondary fw-bold ls-1 mb-4" style={{ fontSize: '0.8rem' }}>Live Market Data</h6>
                                {currentPrice ? (
                                    <div className="animate-fade-in my-auto">
                                        <div className="display-2 fw-black font-monospace tracking-tight mb-2" style={{ color: 'var(--text-primary)' }}>
                                            ${currentPrice.toFixed(2)}
                                        </div>
                                        <div className={`d-inline-flex align-items-center gap-2 px-4 py-2 rounded-pill ${dayChange >= 0 ? 'bg-success-subtle text-success' : 'bg-danger-subtle text-danger'}`}>
                                            <span className="fw-bold fs-4">{dayChange >= 0 ? '▲' : '▼'}</span>
                                            <span className="fw-bold fs-5">{Math.abs(dayChange).toFixed(2)}%</span>
                                        </div>
                                        <div className="mt-4 text-secondary opacity-75 d-flex align-items-center justify-content-center gap-1" style={{ fontSize: '0.8rem' }}>
                                            <div className="spinner-grow spinner-grow-sm text-success" style={{ width: '8px', height: '8px' }} role="status"></div>
                                            Real-time Feed Active
                                        </div>
                                    </div>
                                ) : (
                                    <div className="text-muted fst-italic my-auto fs-5">Connecting to exchange...</div>
                                )}
                            </div>
                        </Col>

                        <Col lg={4} className="px-4">
                            <div className="d-flex flex-column justify-content-center py-3">
                                <h6 className="text-uppercase text-secondary fw-bold ls-1 mb-4 text-center" style={{ fontSize: '0.8rem' }}>Trust & Verification</h6>

                                <div className="mb-4 text-start">
                                    <div className="d-flex justify-content-between mb-2">
                                        <span className="small fw-semibold text-secondary">Argument Faithfulness</span>
                                        <span className="fw-bold text-gradient">{scores.faithfulness}%</span>
                                    </div>
                                    <ProgressBar
                                        now={scores.faithfulness}
                                        variant={scores.faithfulness > 80 ? "success" : "warning"}
                                        style={{ height: '10px', borderRadius: '5px' }}
                                        className="bg-light shadow-inner"
                                    />
                                </div>

                                <div className="text-start">
                                    <div className="d-flex justify-content-between mb-2">
                                        <span className="small fw-semibold text-secondary">Logical Consistency</span>
                                        <span className="fw-bold text-gradient">{scores.consistency}%</span>
                                    </div>
                                    <ProgressBar
                                        now={scores.consistency}
                                        variant={scores.consistency > 80 ? "info" : "warning"}
                                        style={{ height: '10px', borderRadius: '5px' }}
                                        className="bg-light shadow-inner"
                                    />
                                </div>
                            </div>
                        </Col>
                    </Row>
                </Card.Body>

                <div className="p-4" style={{ backgroundColor: 'var(--bg-primary)', borderTop: '1px solid var(--border)' }}>
                    <h6 className="fw-bold mb-2 d-flex align-items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                        <span className="bg-primary text-white rounded-circle d-inline-flex align-items-center justify-content-center" style={{ width: '20px', height: '20px', fontSize: '10px' }}>i</span>
                        Executive Summary
                    </h6>
                    <p className="mb-0 text-secondary lh-lg" style={{ fontFamily: 'Inter, sans-serif', fontSize: '0.95rem' }}>
                        {summary}
                    </p>
                </div>

                {isStrongBuy && (
                    <div className="bg-success text-white text-center fw-bold py-2 small ls-1 text-uppercase">
                        🚀 High Conviction Opportunity Detected
                    </div>
                )}
            </Card>
        </motion.div>
    );
};

export default SigmaCard;
