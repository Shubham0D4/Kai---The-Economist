import React, { useEffect, useRef } from 'react';
import { useCommittee } from '../../context/CommitteeContext';
import { ListGroup, Badge, Card, Button } from 'react-bootstrap';
import { User, Shield, Zap, Scale, Terminal, Gavel, Download } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

import CitationPopover from '../../components/CitationPopover';

const DebateFeed = () => {
    const { debateLogs } = useCommittee();
    const bottomRef = useRef(null);
    const feedRef = useRef(null);

    // Auto-scroll to bottom on new log
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [debateLogs]);

    const getAgentBadge = (agent) => {
        const name = agent?.toLowerCase();
        switch (name) {
            case 'charlie':
                return <Badge bg="primary" className="d-flex align-items-center gap-1"><Shield size={12} /> Charlie</Badge>;
            case 'delta':
                return <Badge bg="warning" text="dark" className="d-flex align-items-center gap-1"><Zap size={12} /> Delta</Badge>;
            case 'gamma':
                return <Badge bg="success" className="d-flex align-items-center gap-1"><Scale size={12} /> Gamma</Badge>;
            case 'sigma':
                return <Badge bg="danger" className="d-flex align-items-center gap-1"><Gavel size={12} /> Sigma</Badge>;
            case 'user':
                return <Badge bg="secondary" className="d-flex align-items-center gap-1"><User size={12} /> User</Badge>;
            case 'system':
                return <Badge bg="dark" className="d-flex align-items-center gap-1"><Terminal size={12} /> System</Badge>;
            default:
                return <Badge bg="info">{agent}</Badge>;
        }
    };

    // Helper to parse citations like [Source: 123]
    const renderMessageWithCitations = (text) => {
        if (!text) return null;

        // Regex to find [Source: XYZ]
        const parts = text.split(/(\[Source:\s*\w+\])/g);

        return parts.map((part, index) => {
            const match = part.match(/^\[Source:\s*(\w+)\]$/);
            if (match) {
                return <CitationPopover key={index} sourceId={match[1]} />;
            }
            return part;
        });
    };

    // Custom markdown components for better styling
    const markdownComponents = {
        h1: ({ node, ...props }) => <h5 className="fw-bold text-primary mt-3 mb-2" {...props} />,
        h2: ({ node, ...props }) => <h6 className="fw-bold text-secondary mt-2 mb-2" {...props} />,
        h3: ({ node, ...props }) => <div className="fw-semibold text-dark mt-2 mb-1" style={{ fontSize: '0.95em' }} {...props} />,
        p: ({ node, ...props }) => <p className="mb-2" style={{ fontSize: '0.9em', lineHeight: '1.6' }} {...props} />,
        ul: ({ node, ...props }) => <ul className="mb-2 ps-3" style={{ fontSize: '0.9em' }} {...props} />,
        ol: ({ node, ...props }) => <ol className="mb-2 ps-3" style={{ fontSize: '0.9em' }} {...props} />,
        li: ({ node, ...props }) => <li className="mb-1" {...props} />,
        strong: ({ node, ...props }) => <strong className="fw-semibold text-dark" {...props} />,
        em: ({ node, ...props }) => <em className="fst-italic text-muted" {...props} />,
        code: ({ node, inline, ...props }) =>
            inline
                ? <code className="bg-light px-1 rounded text-danger" style={{ fontSize: '0.85em' }} {...props} />
                : <pre className="bg-light p-2 rounded border" style={{ fontSize: '0.85em', overflowX: 'auto' }}><code {...props} /></pre>,
        blockquote: ({ node, ...props }) => <blockquote className="border-start border-3 border-primary ps-3 text-muted fst-italic my-2" {...props} />,
    };

    // Export debate feed to PDF
    const exportToPDF = async () => {
        if (!feedRef.current || debateLogs.length === 0) return;

        try {
            // Create a temporary container for PDF rendering
            // We clone the feedRef content to capture the actual rendered Markdown/Styles
            const printContainer = document.createElement('div');
            printContainer.style.position = 'absolute';
            printContainer.style.left = '-9999px';
            printContainer.style.top = '0';
            printContainer.style.width = '800px'; // Fixed width for A4 consistency
            printContainer.style.backgroundColor = 'white';
            printContainer.style.padding = '40px';
            printContainer.style.fontFamily = 'Arial, sans-serif';
            document.body.appendChild(printContainer);

            // Add Header
            const title = document.createElement('h1');
            title.textContent = 'A2A Debate Transcript';
            title.style.marginBottom = '10px';
            title.style.color = '#333';
            printContainer.appendChild(title);

            const timestamp = document.createElement('p');
            timestamp.textContent = `Generated: ${new Date().toLocaleString()}`;
            timestamp.style.marginBottom = '30px';
            timestamp.style.color = '#666';
            printContainer.appendChild(timestamp);

            // Clone the feed content
            // We use cloneNode(true) to get deep copy including all children
            const feedClone = feedRef.current.cloneNode(true);

            // Adjust styles for the clone to ensure it renders fully open
            feedClone.style.maxHeight = 'none';
            feedClone.style.overflow = 'visible';
            feedClone.style.border = 'none';

            // Remove the scrolling anchor from the clone if present in the ref
            // (The ref is on ListGroup, bottomRef is inside it as last item)
            const spacer = feedClone.lastElementChild;
            if (spacer && !spacer.innerHTML) {
                spacer.remove();
            }

            printContainer.appendChild(feedClone);

            // Generate PDF
            const canvas = await html2canvas(printContainer, {
                scale: 2, // Higher scale for better resolution
                useCORS: true,
                logging: false,
                windowWidth: 800
            });

            const imgData = canvas.toDataURL('image/png');
            const pdf = new jsPDF('p', 'mm', 'a4');
            const pdfWidth = pdf.internal.pageSize.getWidth();
            const pdfHeight = pdf.internal.pageSize.getHeight();

            const imgWidth = pdfWidth - 20; // 10mm margin
            const imgHeight = (canvas.height * imgWidth) / canvas.width;

            let heightLeft = imgHeight;
            let position = 10; // Top margin

            // First page
            pdf.addImage(imgData, 'PNG', 10, position, imgWidth, imgHeight);
            heightLeft -= (pdfHeight - 20); // Subtract available page height

            // Subsequent pages
            while (heightLeft > 0) {
                position = heightLeft - imgHeight + 10; // Logic for subsequent pages usually involves shifting image up
                // Actually, standard logic is: position starts at top of next page, but we show a lower slice of image
                // But addImage takes (x, y, w, h). If y is negative, it draws the image higher up.

                // Reset position for new page calculation
                pdf.addPage();

                // Calculate new 'top' position to draw the image such that the next slice shows.
                // If we printed X amount already, we need to shift the image up by X.
                // The 'position' variable in the standard loop is usually -1 * (page_num * visible_height) + margin

                // Let's use a robust calculation:
                // We are at page N. We want to draw the image at y = 10 - (total_height_printed_so_far)
                const currentY = 10 - (imgHeight - heightLeft);

                pdf.addImage(imgData, 'PNG', 10, currentY, imgWidth, imgHeight);
                heightLeft -= (pdfHeight - 20);
            }

            pdf.save(`debate-transcript-${new Date().toISOString().split('T')[0]}.pdf`);

            // Cleanup
            document.body.removeChild(printContainer);
        } catch (error) {
            console.error('Error generating PDF:', error);
            alert('Failed to generate PDF. Please try again.');
        }
    };

    if (debateLogs.length === 0) return null;

    if (debateLogs.length === 0) return null;

    return (
        <Card className="glass-panel mt-4 border-0 shadow-lg" style={{ height: '700px', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <Card.Header className="bg-transparent border-bottom border-light p-4 d-flex justify-content-between align-items-center">
                <div className="d-flex align-items-center gap-2">
                    <div className="bg-success rounded-circle animate-pulse" style={{ width: '10px', height: '10px' }}></div>
                    <h5 className="mb-0 fw-bold text-dark">
                        Live Debate Feed
                    </h5>
                </div>
                <Button
                    variant="outline-secondary"
                    size="sm"
                    onClick={exportToPDF}
                    className="d-flex align-items-center gap-2 rounded-pill px-3 bg-white border-0 shadow-sm"
                >
                    <Download size={14} />
                    <span className="small fw-semibold">Export Transcript</span>
                </Button>
            </Card.Header>
            <Card.Body className="p-0 overflow-auto custom-scrollbar" style={{ backgroundColor: 'rgba(255,255,255,0.3)' }}>
                <ListGroup variant="flush" ref={feedRef} className="p-3">
                    {debateLogs.map((log, index) => (
                        <ListGroup.Item key={index} className="bg-transparent border-0 px-3 py-3 mb-2 rounded-3 hover-bg-light transition-all">
                            <div className="d-flex align-items-start gap-3">
                                <div className="mt-1 shadow-sm rounded-circle bg-white p-1">
                                    {getAgentBadge(log.agent)}
                                </div>
                                <div className="flex-grow-1">
                                    <div className="d-flex justify-content-between align-items-center mb-2">
                                        <span className="small fw-bold text-secondary text-uppercase ls-1" style={{ fontSize: '0.7em' }}>
                                            {log.agent}
                                        </span>
                                        <small className="text-muted opacity-75" style={{ fontSize: '0.75em' }}>
                                            {new Date(log.timestamp).toLocaleTimeString()}
                                        </small>
                                    </div>
                                    <div className="text-primary bg-primary bg-opacity-10 p-4 rounded-4 border border-primary-subtle shadow-sm">
                                        {log.agent === 'system' ? (
                                            <div className="small fst-italic opacity-75">
                                                {renderMessageWithCitations(log.message)}
                                            </div>
                                        ) : (
                                            <div className="markdown-content" style={{ fontSize: '1rem', color: 'var(--text-primary)' }}>
                                                <ReactMarkdown components={markdownComponents}>
                                                    {log.message}
                                                </ReactMarkdown>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </ListGroup.Item>
                    ))}
                    <div ref={bottomRef} />
                </ListGroup>
            </Card.Body>
        </Card>
    );
};

export default DebateFeed;
