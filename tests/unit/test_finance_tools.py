"""
Unit tests for finance_math.py tools.
"""

import pytest
from mcp_server.tools import finance_math

class TestFinanceMath:
    
    def test_pe_ratio(self):
        # Normal case
        assert finance_math.calculate_pe_ratio(100.0, 5.0) == 20.0
        # Zero division protection
        assert finance_math.calculate_pe_ratio(100.0, 0.0) is None
        # Float precision
        assert finance_math.calculate_pe_ratio(100.0, 3.0) == 33.33

    def test_peg_ratio(self):
        # Normal case
        assert finance_math.calculate_peg_ratio(20.0, 10.0) == 2.0
        # Zero division
        assert finance_math.calculate_peg_ratio(20.0, 0.0) is None

    def test_dcf_value(self):
        # Basic DCF
        fcf = [100, 100, 100, 100, 100]
        result = finance_math.calculate_dcf_value(
            free_cash_flows=fcf,
            discount_rate=0.10,
            terminal_growth_rate=0.03,
            shares_outstanding=100
        )
        assert result["enterprise_value"] > 0
        assert result["value_per_share"] > 0
        
        # Invalid inputs (discount <= terminal growth)
        error_result = finance_math.calculate_dcf_value(fcf, 0.02, 0.03, 100)
        assert "error" in error_result

    def test_moving_average(self):
        prices = [10, 20, 30, 40, 50]
        # Normal case
        assert finance_math.calculate_moving_average(prices, 3) == 40.0
        # Insufficient data
        assert finance_math.calculate_moving_average(prices, 10) is None

    def test_volatility(self):
        prices = [100, 101, 102, 103, 104]  # Low volatility
        vol = finance_math.calculate_volatility(prices)
        assert vol < 0.1
        
        volatile_prices = [100, 120, 90, 130, 80]
        high_vol = finance_math.calculate_volatility(volatile_prices)
        assert high_vol > vol
        
        # Single price
        assert finance_math.calculate_volatility([100]) == 0.0

    def test_sharpe_ratio(self):
        # Positive returns
        returns = [0.1, 0.1, 0.1]
        sharpe = finance_math.calculate_sharpe_ratio(returns, risk_free_rate=0.02)
        # Std dev is 0, so should be 0 (check implementation handles zero division)
        # Actually our implementation checks annualized_volatility == 0 -> return 0.0
        assert sharpe == 0.0 
        
        # Varied returns
        returns_var = [0.1, -0.05, 0.15, 0.02]
        sharpe_var = finance_math.calculate_sharpe_ratio(returns_var, risk_free_rate=0.02)
        assert isinstance(sharpe_var, float)
