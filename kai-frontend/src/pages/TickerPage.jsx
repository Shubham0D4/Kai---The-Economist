import React, { useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import SearchInterface from '../components/SearchInterface';
import DebateFeed from '../features/debate/DebateFeed';
import SigmaCard from '../features/debate/SigmaCard';
import AgentStatusGrid from '../features/debate/AgentStatusGrid';
import { useCommittee } from '../context/CommitteeContext';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useMarketSocket } from '../hooks/useMarketSocket';
import { usePriceGlow } from '../hooks/usePriceGlow';
import { getQuote, getHistory } from '../services/api';

const TickerPage = () => {
    const { symbol } = useParams();
    const { finalReport } = useCommittee();
    const resultsRef = useRef(null);

    const [chartData, setChartData] = React.useState([]);
    const [quote, setQuote] = React.useState(null);
    const [period, setPeriod] = React.useState('1d');

    // Live Socket Data
    const socketData = useMarketSocket(symbol);

    // Merge socket data into quote if available
    const displayPrice = socketData?.price || quote?.price;
    const glowClass = usePriceGlow(displayPrice);

    // Auto-scroll to results when report is ready
    useEffect(() => {
        if (finalReport && resultsRef.current) {
            resultsRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [finalReport]);

    // Fetch Data
    useEffect(() => {
        const fetchTickerData = async () => {
            if (!symbol) return;

            // Get Quote
            try {
                const q = await getQuote(symbol);
                setQuote(q);
            } catch (e) {
                console.error(e);
            }

            // Get History
            try {
                const h = await getHistory(symbol, period);
                setChartData(h);
            } catch (e) {
                console.error(e);
            }
        };

        fetchTickerData();
        const interval = setInterval(fetchTickerData, 60000);
        return () => clearInterval(interval);
    }, [symbol, period]);

    return (
        <div className="container-xxl py-4">
            <div className="row g-4">
                {/* Left Column: Chart & Stats */}
                <div className="col-lg-8">
                    <div className="d-flex align-items-baseline gap-3 mb-4">
                        <h1 className="fw-bold display-5 mb-0">{symbol}</h1>
                        <span className="fs-4 text-muted">{quote?.name || 'Loading...'}</span>
                        {quote && (
                            <span className={`badge ${quote.is_positive ? 'bg-success-subtle text-success' : 'bg-danger-subtle text-danger'} rounded-pill px-3`}>
                                {quote.change}
                            </span>
                        )}
                        {displayPrice && (
                            <span className={`fs-4 fw-bold ${glowClass}`} style={{ transition: 'color 0.3s' }}>
                                ${displayPrice}
                            </span>
                        )}
                    </div>

                    {/* Main Chart Area */}
                    <div className="glass-panel p-4 mb-4 shadow-sm" style={{ height: '450px' }}>
                        <div className="d-flex justify-content-between mb-4 align-items-center">
                            <h5 className="fw-bold mb-0">Performance</h5>
                            <div className="btn-group btn-group-sm bg-primary bg-opacity-20 rounded-pill p-1">
                                {['1d', '5d', '1mo', 'ytd', '1y'].map((p) => (
                                    <button
                                        key={p}
                                        onClick={() => setPeriod(p)}
                                        className={`btn btn-sm btn-link text-decoration-none fw-bold px-3 rounded-pill transition-all ${period === p ? 'bg-primary text-white shadow-sm' : 'text-secondary'}`}
                                    >
                                        {p.toUpperCase()}
                                    </button>
                                ))}
                            </div>
                        </div>
                        <ResponsiveContainer width="100%" height={320}>
                            <AreaChart data={chartData}>
                                <defs>
                                    <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" opacity={0.2} />
                                <XAxis
                                    dataKey="name"
                                    axisLine={false}
                                    tickLine={false}
                                    tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                                    dy={10}
                                    minTickGap={30}
                                />
                                <YAxis
                                    domain={['auto', 'auto']}
                                    axisLine={false}
                                    tickLine={false}
                                    tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                                    dx={-10}
                                />
                                <Tooltip
                                    contentStyle={{
                                        borderRadius: '12px',
                                        border: '1px solid var(--border)',
                                        boxShadow: '0 4px 20px rgba(0,0,0,0.4)',
                                        background: 'var(--bg-surface)',
                                        backdropFilter: 'blur(10px)'
                                    }}
                                    itemStyle={{ color: 'var(--brand-accent)', fontWeight: 600 }}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="price"
                                    stroke="var(--brand-accent)"
                                    strokeWidth={3}
                                    fillOpacity={1}
                                    fill="url(#colorPrice)"
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Analysis Section */}
                    <div className="mb-5">
                        <h3 className="fw-bold mb-4">AI Council Analysis</h3>

                        {/* We reuse the SearchInterface but pre-filled logic would be here */}
                        {/* For now, just show the interface to initiate */}
                        <SearchInterface initialTicker={symbol} />

                        <div className="mt-4">
                            <AgentStatusGrid />
                        </div>

                        <div className="mt-4">
                            <DebateFeed />
                        </div>

                        <div ref={resultsRef}>
                            <SigmaCard />
                        </div>
                    </div>
                </div>

                {/* Right Column: News & Fundamentals */}
                <div className="col-lg-4">
                    <div className="sticky-top" style={{ top: '20px', zIndex: 10 }}>
                        <div className="glass-panel p-4 mb-4">
                            <h5 className="fw-bold mb-3">Key Statistics</h5>
                            <div className="d-flex justify-content-between py-2 border-bottom border-light">
                                <span className="text-muted">Market Cap</span>
                                <span className="fw-semibold">{quote?.market_cap ? (quote.market_cap / 1e9).toFixed(2) + 'B' : '...'}</span>
                            </div>
                            <div className="d-flex justify-content-between py-2 border-bottom border-light">
                                <span className="text-muted">P/E Ratio</span>
                                <span className="fw-semibold">{quote?.pe_ratio ? parseFloat(quote.pe_ratio).toFixed(2) : '-'}</span>
                            </div>
                            <div className="d-flex justify-content-between py-2 border-bottom border-light">
                                <span className="text-muted">Dividend Yield</span>
                                <span className="fw-semibold">{quote?.dividend_yield || '-'}</span>
                            </div>
                            <div className="d-flex justify-content-between py-2">
                                <span className="text-muted">52W Range</span>
                                <span className="fw-semibold">{quote?.low_52w} - {quote?.high_52w}</span>
                            </div>
                        </div>

                        <div className="glass-panel p-4">
                            <h5 className="fw-bold mb-3">Latest News</h5>
                            <div className="d-flex flex-column gap-3">
                                <div className="d-flex gap-3">
                                    <div className="bg-primary bg-opacity-10 rounded" style={{ width: '60px', height: '60px' }}></div>
                                    <div>
                                        <div className="small text-muted mb-1">WSJ • 1h</div>
                                        <a href="#" className="fw-semibold text-decoration-none text-truncate-2-lines" style={{ fontSize: '0.9rem', color: 'var(--text-primary)' }}>Apple faces unexpected production delays in Asia</a>
                                    </div>
                                </div>
                                <div className="d-flex gap-3">
                                    <div className="bg-primary bg-opacity-10 rounded" style={{ width: '60px', height: '60px' }}></div>
                                    <div>
                                        <div className="small text-muted mb-1">TechCrunch • 3h</div>
                                        <a href="#" className="fw-semibold text-decoration-none text-truncate-2-lines" style={{ fontSize: '0.9rem', color: 'var(--text-primary)' }}>App Store revenue hits record highs in Q4</a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TickerPage;
