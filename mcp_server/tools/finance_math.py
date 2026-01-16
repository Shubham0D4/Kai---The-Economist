"""
Deterministic financial calculation utilities.
Provides pure Python functions for financial metrics used by Gamma agent.
"""

from typing import Dict, List, Optional
from datetime import datetime


def calculate_pe_ratio(price: float, earnings_per_share: float) -> Optional[float]:
    """
    Calculate Price-to-Earnings ratio.
    
    Args:
        price: Current stock price
        earnings_per_share: Earnings per share (EPS)
        
    Returns:
        PE ratio or None if EPS is zero
    """
    if earnings_per_share == 0:
        return None
    return round(price / earnings_per_share, 2)


def calculate_peg_ratio(
    pe_ratio: float,
    earnings_growth_rate: float
) -> Optional[float]:
    """
    Calculate Price/Earnings to Growth (PEG) ratio.
    
    Args:
        pe_ratio: Price-to-Earnings ratio
        earnings_growth_rate: Expected earnings growth rate (as percentage)
        
    Returns:
        PEG ratio or None if growth rate is zero
    """
    if earnings_growth_rate == 0:
        return None
    return round(pe_ratio / earnings_growth_rate, 2)


def calculate_dcf_value(
    free_cash_flows: List[float],
    discount_rate: float,
    terminal_growth_rate: float,
    shares_outstanding: float
) -> Dict:
    """
    Calculate Discounted Cash Flow (DCF) valuation.
    
    Args:
        free_cash_flows: List of projected free cash flows for future years
        discount_rate: Discount rate (WACC) as decimal (e.g., 0.10 for 10%)
        terminal_growth_rate: Perpetual growth rate as decimal (e.g., 0.03 for 3%)
        shares_outstanding: Number of shares outstanding
        
    Returns:
        Dictionary with DCF analysis results
    """
    if discount_rate <= terminal_growth_rate:
        return {
            "error": "Discount rate must be greater than terminal growth rate"
        }
    
    # Calculate present value of projected cash flows
    pv_cash_flows = []
    for year, fcf in enumerate(free_cash_flows, start=1):
        pv = fcf / ((1 + discount_rate) ** year)
        pv_cash_flows.append(pv)
    
    sum_pv_cash_flows = sum(pv_cash_flows)
    
    # Calculate terminal value
    last_fcf = free_cash_flows[-1]
    terminal_fcf = last_fcf * (1 + terminal_growth_rate)
    terminal_value = terminal_fcf / (discount_rate - terminal_growth_rate)
    
    # Discount terminal value to present
    years = len(free_cash_flows)
    pv_terminal_value = terminal_value / ((1 + discount_rate) ** years)
    
    # Calculate enterprise value and equity value per share
    enterprise_value = sum_pv_cash_flows + pv_terminal_value
    value_per_share = enterprise_value / shares_outstanding
    
    return {
        "enterprise_value": round(enterprise_value, 2),
        "value_per_share": round(value_per_share, 2),
        "pv_cash_flows": round(sum_pv_cash_flows, 2),
        "pv_terminal_value": round(pv_terminal_value, 2),
        "terminal_value": round(terminal_value, 2),
        "discount_rate": discount_rate,
        "terminal_growth_rate": terminal_growth_rate,
        "projection_years": years
    }


def calculate_moving_average(prices: List[float], period: int) -> Optional[float]:
    """
    Calculate simple moving average.
    
    Args:
        prices: List of prices (most recent last)
        period: Number of periods for the average
        
    Returns:
        Moving average or None if insufficient data
    """
    if len(prices) < period:
        return None
    
    recent_prices = prices[-period:]
    return round(sum(recent_prices) / period, 2)


def calculate_volatility(prices: List[float]) -> float:
    """
    Calculate price volatility (standard deviation of returns).
    
    Args:
        prices: List of prices (chronological order)
        
    Returns:
        Volatility as standard deviation of daily returns
    """
    if len(prices) < 2:
        return 0.0
    
    # Calculate daily returns
    returns = []
    for i in range(1, len(prices)):
        daily_return = (prices[i] - prices[i-1]) / prices[i-1]
        returns.append(daily_return)
    
    # Calculate mean return
    mean_return = sum(returns) / len(returns)
    
    # Calculate variance
    variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
    
    # Standard deviation (volatility)
    volatility = variance ** 0.5
    
    return round(volatility, 4)


def calculate_sharpe_ratio(
    returns: List[float],
    risk_free_rate: float = 0.02
) -> float:
    """
    Calculate Sharpe ratio (risk-adjusted return).
    
    Args:
        returns: List of periodic returns (as decimals)
        risk_free_rate: Annual risk-free rate (default: 2%)
        
    Returns:
        Sharpe ratio
    """
    if len(returns) == 0:
        return 0.0
    
    # Calculate average return
    avg_return = sum(returns) / len(returns)
    
    # Annualize (assuming daily returns)
    annualized_return = avg_return * 252
    
    # Calculate standard deviation
    mean_return = sum(returns) / len(returns)
    variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
    std_dev = variance ** 0.5
    
    # Annualize volatility
    annualized_volatility = std_dev * (252 ** 0.5)
    
    if annualized_volatility < 1e-9:
        return 0.0
    
    # Sharpe ratio
    sharpe = (annualized_return - risk_free_rate) / annualized_volatility
    
    return round(sharpe, 2)


# MCP Tool Functions (wrapped for MCP exposure)

def calculate_valuation_metrics(
    price: float,
    eps: float,
    growth_rate: float,
    free_cash_flows: Optional[List[float]] = None,
    discount_rate: float = 0.10,
    terminal_growth: float = 0.03,
    shares_outstanding: Optional[float] = None
) -> Dict:
    """
    MCP tool to calculate comprehensive valuation metrics.
    
    Used by Gamma agent for quantitative valuation analysis.
    
    Args:
        price: Current stock price
        eps: Earnings per share
        growth_rate: Expected earnings growth rate (as percentage, e.g., 15 for 15%)
        free_cash_flows: Optional list of projected FCFs for DCF analysis
        discount_rate: WACC for DCF (default: 0.10)
        terminal_growth: Perpetual growth rate for DCF (default: 0.03)
        shares_outstanding: Number of shares for DCF calculation
        
    Returns:
        Dictionary with PE ratio, PEG ratio, and optionally DCF valuation
    """
    results = {}
    
    # PE Ratio
    pe_ratio = calculate_pe_ratio(price, eps)
    results["pe_ratio"] = pe_ratio
    
    # PEG Ratio
    if pe_ratio is not None:
        peg_ratio = calculate_peg_ratio(pe_ratio, growth_rate)
        results["peg_ratio"] = peg_ratio
    
    # DCF Analysis (if data provided)
    if free_cash_flows and shares_outstanding:
        dcf_results = calculate_dcf_value(
            free_cash_flows,
            discount_rate,
            terminal_growth,
            shares_outstanding
        )
        results["dcf_analysis"] = dcf_results
    
    results["input_price"] = price
    results["input_eps"] = eps
    results["input_growth_rate"] = growth_rate
    
    return results


def calculate_risk_metrics(
    prices: List[float],
    returns: Optional[List[float]] = None,
    risk_free_rate: float = 0.02
) -> Dict:
    """
    MCP tool to calculate risk metrics.
    
    Used by Gamma agent for risk assessment.
    
    Args:
        prices: List of historical prices
        returns: Optional list of returns (calculated from prices if not provided)
        risk_free_rate: Annual risk-free rate (default: 2%)
        
    Returns:
        Dictionary with volatility, Sharpe ratio, and moving averages
    """
    results = {}
    
    # Volatility
    volatility = calculate_volatility(prices)
    results["volatility"] = volatility
    
    # Moving averages
    ma_50 = calculate_moving_average(prices, 50)
    ma_200 = calculate_moving_average(prices, 200)
    
    results["ma_50"] = ma_50
    results["ma_200"] = ma_200
    
    # Sharpe ratio (if returns provided or can be calculated)
    if returns:
        sharpe = calculate_sharpe_ratio(returns, risk_free_rate)
        results["sharpe_ratio"] = sharpe
    elif len(prices) >= 2:
        # Calculate returns from prices
        calculated_returns = []
        for i in range(1, len(prices)):
            daily_return = (prices[i] - prices[i-1]) / prices[i-1]
            calculated_returns.append(daily_return)
        sharpe = calculate_sharpe_ratio(calculated_returns, risk_free_rate)
        results["sharpe_ratio"] = sharpe
    
    results["price_count"] = len(prices)
    
    return results


# For testing
if __name__ == "__main__":
    import json
    
    # Test valuation metrics
    print("=== Valuation Metrics ===")
    valuation = calculate_valuation_metrics(
        price=150.0,
        eps=6.5,
        growth_rate=15.0,
        free_cash_flows=[10000, 11000, 12100, 13310, 14641],
        discount_rate=0.10,
        terminal_growth=0.03,
        shares_outstanding=1000
    )
    print(json.dumps(valuation, indent=2))
    
    # Test risk metrics
    print("\n=== Risk Metrics ===")
    test_prices = [100, 102, 101, 105, 103, 107, 106, 110, 108, 112]
    risk = calculate_risk_metrics(test_prices)
    print(json.dumps(risk, indent=2))
