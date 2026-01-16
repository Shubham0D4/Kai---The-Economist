import { useState, useEffect, useRef } from 'react';

// Use a singleton based approach for the socket to avoid multiple connections?
// For now, simple hook implementation.

const FINNHUB_KEY = import.meta.env.VITE_FINNHUB_API_KEY;

export const useMarketSocket = (symbol) => {
    const [priceData, setPriceData] = useState(null);
    const socketRef = useRef(null);

    useEffect(() => {
        // If no key or no symbol, do nothing (will fall back to polling in parent)
        if (!FINNHUB_KEY || !symbol) return;

        console.log(`🔌 Connecting to Finnhub WS for ${symbol}...`);

        // Connect
        const socket = new WebSocket(`wss://ws.finnhub.io?token=${FINNHUB_KEY}`);
        socketRef.current = socket;

        socket.onopen = () => {
            console.log('✅ Finnhub WS Connected');
            socket.send(JSON.stringify({ 'type': 'subscribe', 'symbol': symbol }));
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'trade' && data.data && data.data.length > 0) {
                // Get the latest trade
                const trade = data.data[data.data.length - 1]; // Last one is latest
                setPriceData({
                    price: trade.p,
                    time: trade.t,
                    volume: trade.v
                });
            }
        };

        socket.onerror = (error) => {
            console.error('❌ Finnhub WS Error:', error);
        };

        return () => {
            if (socket.readyState === 1) {
                socket.send(JSON.stringify({ 'type': 'unsubscribe', 'symbol': symbol }));
                socket.close();
            }
        };
    }, [symbol]);

    return priceData;
};
