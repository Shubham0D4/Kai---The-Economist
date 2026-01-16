import { useState, useEffect, useRef } from 'react';

export const usePriceGlow = (currentPrice) => {
    const [glowClass, setGlowClass] = useState('');
    const prevPriceRef = useRef(currentPrice);

    useEffect(() => {
        if (currentPrice === null || currentPrice === undefined) return;

        const prevPrice = prevPriceRef.current;

        if (prevPrice !== null && prevPrice !== undefined) {
            if (currentPrice > prevPrice) {
                setGlowClass('glow-green-flash');
            } else if (currentPrice < prevPrice) {
                setGlowClass('glow-red-flash');
            }
        }

        // Update ref
        prevPriceRef.current = currentPrice;

        // Reset animation class after it plays (approx 1s)
        const timer = setTimeout(() => {
            setGlowClass('');
        }, 1200);

        return () => clearTimeout(timer);

    }, [currentPrice]);

    return glowClass;
};
