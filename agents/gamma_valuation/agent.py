"""
Gamma - Valuation Analysis Agent
Performs quantitative valuation using DCF, multiples, and risk metrics.
"""

import os
import sys
import json
import argparse
import time
import random
from typing import Dict, Optional, List

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from coordinator.personas import RiskPersona, get_gamma_system_instruction
from mcp_server.tools.finance_math import calculate_valuation_metrics, calculate_risk_metrics

# Import Multi-LLM Client
from coordinator.llm_client import MultiLLMClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class GammaAgent:
    """
    Gamma - Valuation Analysis Specialist
    
    Performs quantitative valuation using DCF, multiples, and risk metrics.
    Adjusts parameters based on risk persona (Zen vs Alpha).
    """
    
    def __init__(self, persona: RiskPersona = RiskPersona.ZEN):
        """
        Initialize Gamma agent.
        
        Args:
            persona: Risk persona to apply (Zen or Alpha)
        """
        self.persona = persona
        self.name = "Gamma"
        self.role = "Valuation Analysis Specialist"
        
        # Initialize hybrid model with system instruction
        system_instruction = get_gamma_system_instruction(persona)
        self.model = MultiLLMClient(system_instruction=system_instruction)
    
    def analyze(
        self,
        ticker: str,
        price: Optional[float] = None,
        eps: Optional[float] = None,
        growth_rate: Optional[float] = None,
        free_cash_flows: Optional[List[float]] = None,
        shares_outstanding: Optional[float] = None,
        historical_prices: Optional[List[float]] = None
    ) -> Dict:
        """
        Perform valuation analysis on a ticker.
        
        Args:
            ticker: Stock ticker symbol
            price: Current stock price
            eps: Earnings per share
            growth_rate: Expected earnings growth rate (percentage)
            free_cash_flows: Optional projected FCFs for DCF
            shares_outstanding: Number of shares (required for DCF)
            historical_prices: Optional price history for risk metrics
            
        Returns:
            Analysis results with valuation assessment
        """
        print(f"[Gamma] Calculating valuation metrics for {ticker}...")
        
        # Adjust discount rate based on persona
        if self.persona == RiskPersona.ZEN:
            discount_rate = 0.12  # Higher discount rate (more conservative)
            terminal_growth = 0.025  # Lower terminal growth
        elif self.persona == RiskPersona.ALPHA:
            discount_rate = 0.08  # Lower discount rate (more aggressive)
            terminal_growth = 0.035  # Higher terminal growth
        else:  # SIGMA
            discount_rate = 0.10  # Standard WACC
            terminal_growth = 0.03  # Standard terminal growth
        
        # Calculate valuation metrics if possible
        valuation_data = {}
        if all(v is not None for v in [price, eps, growth_rate]):
            valuation_data = calculate_valuation_metrics(
                price=price,
                eps=eps,
                growth_rate=growth_rate,
                free_cash_flows=free_cash_flows,
                discount_rate=discount_rate,
                terminal_growth=terminal_growth,
                shares_outstanding=shares_outstanding
            )
        
        # Calculate risk metrics if historical prices provided
        risk_data = None
        if historical_prices and len(historical_prices) >= 10:
            print(f"[Gamma] Calculating risk metrics for {ticker}...")
            risk_data = calculate_risk_metrics(prices=historical_prices)
        
        # Prepare analysis prompt
        valuation_summary = json.dumps(valuation_data, indent=2)
        risk_summary = json.dumps(risk_data, indent=2) if risk_data else "No risk data available"
        
        prompt = f"""
Analyze the valuation for {ticker} based on quantitative metrics.

Current Price: ${price}
EPS: ${eps}
Expected Growth Rate: {growth_rate}%

Valuation Metrics:
{valuation_summary}

Risk Metrics:
{risk_summary}

Discount Rate Used: {discount_rate*100}% (adjusted for {self.persona.value} persona)
Terminal Growth Rate: {terminal_growth*100}%

Based on your expertise in quantitative valuation and your current risk persona, provide:

1. **Valuation Assessment**: Evaluate if the stock is overvalued, fairly valued, or undervalued
2. **PE/PEG Analysis**: Interpret the PE and PEG ratios in context
3. **DCF Analysis**: If available, assess the DCF valuation and intrinsic value
4. **Risk Metrics**: Analyze volatility, Sharpe ratio, and risk-adjusted returns
5. **Sensitivity Analysis**: Discuss how assumptions impact valuation
6. **Recommendation**: Provide your quantitative view (Bullish/Neutral/Bearish) with confidence level

Format your response as a structured analysis with clear sections.
"""
        
        # Generate analysis with fallback logic
        print(f"[Gamma] Analyzing valuation for {ticker} with {self.persona.value} persona...")
        
        try:
            response = self.model.generate_content(prompt)
            
            return {
                "agent": self.name,
                "role": self.role,
                "ticker": ticker,
                "persona": self.persona.value,
                "valuation_metrics": valuation_data,
                "risk_metrics": risk_data,
                "parameters": {
                    "discount_rate": discount_rate,
                    "terminal_growth": terminal_growth,
                    "current_price": price,
                    "eps": eps,
                    "growth_rate": growth_rate
                },
                "analysis": response.text,
                "token_usage": {
                    "prompt_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0),
                    "candidates_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0),
                    "total_tokens": getattr(response.usage_metadata, 'total_token_count', 0)
                }
            }
        except Exception as e:
            return {
                "agent": self.name,
                "ticker": ticker,
                "persona": self.persona.value,
                "error": f"LLM Generation Failed: {str(e)}",
                "analysis": None
            }
    
    def get_agent_card(self) -> Dict:
        """
        Get A2A Agent Card for Gamma by loading the agent.json file.
        """
        card_path = os.path.join(os.path.dirname(__file__), "agent.json")
        try:
            with open(card_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[Gamma] Error loading agent card: {e}")
            return {
                "name": "Gamma",
                "role": "Valuation Analysis Specialist",
                "persona_support": ["zen", "alpha", "balanced"]
            }


def main():
    """Main entry point for testing Gamma agent."""
    parser = argparse.ArgumentParser(description="Gamma - Valuation Analysis Agent")
    parser.add_argument("--ticker", type=str, required=True, help="Stock ticker symbol")
    parser.add_argument("--persona", type=str, default="zen", choices=["zen", "alpha"], help="Risk persona")
    parser.add_argument("--price", type=float, required=True, help="Current stock price")
    parser.add_argument("--eps", type=float, required=True, help="Earnings per share")
    parser.add_argument("--growth-rate", type=float, required=True, help="Expected growth rate (%)")
    
    args = parser.parse_args()
    
    # Create agent with specified persona
    persona = RiskPersona.ZEN if args.persona == "zen" else RiskPersona.ALPHA
    gamma = GammaAgent(persona=persona)
    
    # Example historical prices (in production, fetch from data source)
    example_prices = [args.price * (1 + i*0.01) for i in range(-50, 1)]
    
    # Perform analysis
    result = gamma.analyze(
        ticker=args.ticker,
        price=args.price,
        eps=args.eps,
        growth_rate=args.growth_rate,
        historical_prices=example_prices
    )
    
    # Print results
    print("\n" + "="*80)
    print(f"GAMMA'S VALUATION ANALYSIS - {args.ticker.upper()}")
    print(f"Persona: {persona.value.upper()}")
    print("="*80 + "\n")
    
    print(result["analysis"])
    print("\n" + "="*80)
    print(f"PE Ratio: {result['valuation_metrics'].get('pe_ratio')}")
    print(f"PEG Ratio: {result['valuation_metrics'].get('peg_ratio')}")
    print(f"Discount Rate: {result['parameters']['discount_rate']*100}%")
    print("="*80)


if __name__ == "__main__":
    main()
