import React, { useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { TrendingUp, Activity, ArrowRight, Search, Globe, ChevronRight, BarChart2, Zap } from 'lucide-react';
import { Dropdown } from 'react-bootstrap';
import SearchInterface from '../components/SearchInterface';
import { getIndices, getQuote } from '../services/api';
import AgentStatusGrid from '../features/debate/AgentStatusGrid';
import DebateFeed from '../features/debate/DebateFeed';
import SigmaCard from '../features/debate/SigmaCard';
import { useCommittee } from '../context/CommitteeContext';

const Dashboard = () => {
    const navigate = useNavigate();
    const { finalReport, debateLogs } = useCommittee();
    const resultsRef = useRef(null);

    // Auto-scroll to results when report is ready
    useEffect(() => {
        if (finalReport && resultsRef.current) {
            resultsRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [finalReport]);

    const [indices, setIndices] = React.useState([]);
    const [watchlist, setWatchlist] = React.useState([
        { symbol: 'NVDA', name: 'NVIDIA' },
        { symbol: 'AAPL', name: 'Apple' },
        { symbol: 'TSLA', name: 'Tesla' },
        { symbol: 'AMD', name: 'AMD' },
        { symbol: 'MSFT', name: 'Microsoft' },
        { symbol: 'GOOGL', name: 'Alphabet' },
        { symbol: 'AMZN', name: 'Amazon' },
        { symbol: 'BTC-USD', name: 'Bitcoin' },
        { symbol: 'ETH-USD', name: 'Ethereum' }
    ]);
    const [watchlistData, setWatchlistData] = React.useState([]);

    useEffect(() => {
        const fetchData = async () => {
            // Fetch Indices
            const indicesData = await getIndices();
            setIndices(indicesData);

            // Fetch Watchlist Quotes
            const quotes = await Promise.all(
                watchlist.map(async (item) => {
                    try {
                        const quote = await getQuote(item.symbol);
                        return { ...item, ...quote };
                    } catch (e) {
                        return item; // Fallback
                    }
                })
            );
            setWatchlistData(quotes);
        };

        fetchData();
        const interval = setInterval(fetchData, 60000); // Poll every minute
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="kai-layout-center py-4">
            <div className="row g-4 justify-content-center">

                {/* MOBILE VIEW: Quick Access Dropdowns */}
                <div className="col-12 d-lg-none mb-4">
                    <div className="d-flex gap-2">
                        <Dropdown className="flex-grow-1">
                            <Dropdown.Toggle variant="outline-primary" className="w-100 rounded-pill py-2 bg-primary bg-opacity-10 d-flex align-items-center justify-content-center gap-2">
                                <BarChart2 size={18} />
                                <span className="fw-semibold">Watchlist</span>
                            </Dropdown.Toggle>
                            <Dropdown.Menu className="glass-panel border-0 shadow-lg p-2 w-100 mt-2 custom-scrollbar" style={{ maxHeight: '300px', overflowY: 'auto' }}>
                                {watchlistData.map((stock) => (
                                    <Dropdown.Item
                                        key={stock.symbol}
                                        onClick={() => navigate(`/ticker/${stock.symbol}`)}
                                        className="rounded-3 p-3 hover-bg-light transition-all mb-1 border-bottom border-light border-opacity-10"
                                    >
                                        <div className="d-flex justify-content-between align-items-center">
                                            <div>
                                                <div className="fw-bold">{stock.symbol}</div>
                                                <div className="small text-muted">{stock.name}</div>
                                            </div>
                                            <div className="text-end">
                                                <div className="fw-bold">${stock.price || '...'}</div>
                                                <div className={`small fw-bold ${stock.change?.startsWith('+') ? 'text-success' : 'text-danger'}`}>
                                                    {stock.change}
                                                </div>
                                            </div>
                                        </div>
                                    </Dropdown.Item>
                                ))}
                            </Dropdown.Menu>
                        </Dropdown>

                        <Dropdown className="flex-grow-1">
                            <Dropdown.Toggle variant="outline-success" className="w-100 rounded-pill py-2 bg-success bg-opacity-10 d-flex align-items-center justify-content-center gap-2">
                                <Globe size={18} />
                                <span className="fw-semibold">Market Pulse</span>
                            </Dropdown.Toggle>
                            <Dropdown.Menu className="glass-panel border-0 shadow-lg p-2 w-100 mt-2 custom-scrollbar" style={{ maxHeight: '400px', overflowY: 'auto' }}>
                                <Dropdown.Header className="text-uppercase small fw-bold text-muted ls-1">Global Indices</Dropdown.Header>
                                {indices.map((idx) => (
                                    <Dropdown.Item key={idx.name} className="rounded-3 p-3 pointer-events-none">
                                        <div className="d-flex justify-content-between align-items-center">
                                            <span className="fw-semibold text-secondary">{idx.name}</span>
                                            <div className="text-end">
                                                <div className="fw-bold">{idx.value}</div>
                                                <div className={`small fw-bold ${idx.positive ? 'text-success' : 'text-danger'}`}>{idx.change}</div>
                                            </div>
                                        </div>
                                    </Dropdown.Item>
                                ))}
                                <Dropdown.Divider className="border-light border-opacity-10" />
                                <Dropdown.Header className="text-uppercase small fw-bold text-muted ls-1">Live Wire Feed</Dropdown.Header>
                                <div className="p-2 d-flex flex-column gap-2">
                                    <div className="small p-2 rounded-3 hover-bg-light">
                                        <div className="fw-bold text-primary mb-1">Macro • 12m</div>
                                        <div className="text-wrap">Fed Chair Powell hints at "cautious approach" to rate cuts</div>
                                    </div>
                                    <div className="small p-2 rounded-3 hover-bg-light">
                                        <div className="fw-bold text-success mb-1">Tech • 45m</div>
                                        <div className="text-wrap">OpenAI releases new reasoning model, sparking rally</div>
                                    </div>
                                </div>
                            </Dropdown.Menu>
                        </Dropdown>
                    </div>
                </div>

                {/* LEFT SIDEBAR: Watchlist (Desktop) */}
                <div className="col-lg-2 d-none d-lg-block desktop-end-bar-left">
                    <div className="sticky-top" style={{ top: '24px' }}>
                        <div className="glass-panel p-3 shadow-sm mb-4 border-0">
                            <div className="d-flex align-items-center gap-2 mb-3 px-2">
                                <BarChart2 size={20} className="text-primary" />
                                <h6 className="fw-bold mb-0">Watchlist</h6>
                            </div>
                            <div className="d-flex flex-column gap-2">
                                {watchlistData.map((stock) => (
                                    <div
                                        key={stock.symbol}
                                        onClick={() => navigate(`/ticker/${stock.symbol}`)}
                                        className="d-flex justify-content-between align-items-center p-2 rounded-3 hover-bg-light transition-all cursor-pointer"
                                    >
                                        <div>
                                            <div className="fw-bold" style={{ fontSize: '0.9rem' }}>{stock.symbol}</div>
                                            <div className="small text-muted" style={{ fontSize: '0.7rem', display: 'block', maxWidth: '80px' }}>{stock.name}</div>
                                        </div>
                                        <div className="text-end">
                                            <div className="fw-semibold" style={{ fontSize: '0.85rem' }}>${stock.price || '...'}</div>
                                            {stock.change && (
                                                <div className={`small fw-bold ${stock.change.startsWith('+') ? 'text-success' : 'text-danger'}`} style={{ fontSize: '0.7rem' }}>
                                                    {stock.change}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                            <div className="mt-3 text-center">
                                <button className="btn btn-sm btn-link text-decoration-none text-muted opacity-50">View All</button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* CENTER COLUMN: Command Center */}
                <div className="col-lg-7 px-lg-5">
                    {/* Header */}
                    <div className="text-center mb-5 animate-fade-in-up">
                        <div className="d-inline-flex align-items-center justify-content-center gap-2 mb-2 px-3 py-1 rounded-pill bg-primary bg-opacity-10 text-primary border border-primary-subtle shadow-sm">
                            <Zap size={14} fill="currentColor" />
                            <span className="small fw-bold text-uppercase ls-1">Kai Consensus Protocol 2.0</span>
                        </div>
                        <h1 className="display-5 fw-black ls-tight mb-2">
                            <span className="text-gradient">Command Center</span>
                        </h1>
                        <p className="text-secondary opacity-75 mx-auto" style={{ maxWidth: '450px' }}>
                            Orchestrate autonomous AI agents to analyze complex financial data in real-time.
                        </p>
                    </div>

                    {/* Search Interface (The Core) */}
                    <div className="mb-5">
                        <SearchInterface />
                    </div>

                    {/* Analysis Results (Conditionally Visible) */}
                    {(debateLogs.length > 0 || finalReport) && (
                        <div className="animate-slide-up">
                            <div className="d-flex align-items-center gap-3 mb-3">
                                <div className="h-px bg-light flex-grow-1"></div>
                                <span className="small text-uppercase text-muted fw-bold ls-1">Active Analysis</span>
                                <div className="h-px bg-light flex-grow-1"></div>
                            </div>

                            <AgentStatusGrid />

                            <DebateFeed />

                            <div ref={resultsRef} className="mt-5 pt-5 pb-5">
                                {finalReport && (
                                    <div className="animate-scale-in">
                                        <div className="d-flex align-items-center gap-3 mb-4 opacity-75">
                                            <div className="h-px bg-secondary flex-grow-1 opacity-25"></div>
                                            <span className="small text-uppercase text-muted fw-bold ls-1">Consensus Verdict</span>
                                            <div className="h-px bg-secondary flex-grow-1 opacity-25"></div>
                                        </div>
                                        <SigmaCard />
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>

                {/* RIGHT SIDEBAR: Market Pulse (Desktop) */}
                <div className="col-lg-3 d-none d-lg-block desktop-end-bar-right">
                    <div className="sticky-top" style={{ top: '20px' }}>
                        {/* Indices */}
                        <div className="glass-panel p-3 shadow-sm mb-4">
                            <div className="d-flex align-items-center gap-2 mb-3 px-2">
                                <Activity size={20} className="text-success" />
                                <h6 className="fw-bold mb-0">Global Indices</h6>
                            </div>
                            <div className="d-flex flex-column gap-3">
                                {indices.map((idx) => (
                                    <div key={idx.name} className="d-flex justify-content-between align-items-center px-2">
                                        <span className="fw-semibold text-secondary small">{idx.name}</span>
                                        <div className="text-end">
                                            <div className="fw-bold fs-6">{idx.value}</div>
                                            <div className={`small fw-bold ${idx.positive ? 'text-success' : 'text-danger'}`}>{idx.change}</div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* News */}
                        <div className="glass-panel p-3 shadow-sm">
                            <div className="d-flex align-items-center gap-2 mb-3 px-2">
                                <Globe size={20} className="text-info" />
                                <h6 className="fw-bold mb-0">Live Wire</h6>
                            </div>
                            <div className="d-flex flex-column gap-3">
                                <div className="border-bottom border-light pb-2 px-2 hover-bg-light rounded transition-all p-2 cursor-pointer">
                                    <div className="d-flex justify-content-between mb-1">
                                        <span className="badge bg-primary bg-opacity-20 text-primary border border-primary-subtle">Macro</span>
                                        <small className="text-muted">12m ago</small>
                                    </div>
                                    <a href="#" className="fw-semibold text-decoration-none small text-truncate-2-lines">
                                        Fed Chair Powell hints at "cautious approach" to rate cuts in 2026
                                    </a>
                                </div>
                                <div className="border-bottom border-light pb-2 px-2 hover-bg-light rounded transition-all p-2 cursor-pointer">
                                    <div className="d-flex justify-content-between mb-1">
                                        <span className="badge bg-primary bg-opacity-20 text-primary border border-primary-subtle">Tech</span>
                                        <small className="text-muted">45m ago</small>
                                    </div>
                                    <a href="#" className="fw-semibold text-decoration-none small text-truncate-2-lines">
                                        OpenAI releases new reasoning model, sparking rally in semi stocks
                                    </a>
                                </div>
                                <div className="px-2 hover-bg-light rounded transition-all p-2 cursor-pointer">
                                    <div className="d-flex justify-content-between mb-1">
                                        <span className="badge bg-primary bg-opacity-20 text-primary border border-primary-subtle">Energy</span>
                                        <small className="text-muted">1h ago</small>
                                    </div>
                                    <a href="#" className="fw-semibold text-decoration-none small text-truncate-2-lines">
                                        Oil stabilizes as OPEC+ meeting concludes with no output changes
                                    </a>
                                </div>
                            </div>
                        </div>

                        {/* Ad / Promo Area */}
                        <div className="mt-4 text-center">
                            <small className="text-muted opacity-50">Data delayed by 15 mins</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
