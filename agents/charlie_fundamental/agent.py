"""
Charlie - Fundamental Analysis Agent
Focuses on value investing, MOAT analysis, and financial health.
"""

import os
import sys
import json
import argparse
import time
import random
from typing import Dict, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from coordinator.personas import RiskPersona, get_charlie_system_instruction
from mcp_server.tools.sec_filings import fetch_filing_data

# Import Multi-LLM Client
from coordinator.llm_client import MultiLLMClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class CharlieAgent:
    """
    Charlie - Fundamental Analysis Specialist
    
    Analyzes SEC filings, balance sheets, and competitive advantages.
    Adjusts analysis based on risk persona (Zen vs Alpha).
    """
    
    def __init__(self, persona: RiskPersona = RiskPersona.ZEN):
        """
        Initialize Charlie agent.
        
        Args:
            persona: Risk persona to apply (Zen or Alpha)
        """
        self.persona = persona
        self.name = "Charlie"
        self.role = "Fundamental Analysis Specialist"
        
        # Initialize hybrid model with system instruction
        system_instruction = get_charlie_system_instruction(persona)
        self.model = MultiLLMClient(system_instruction=system_instruction)
    
    def analyze(self, ticker: str, filing_type: str = "10-K") -> Dict:
        """
        Perform fundamental analysis on a ticker.
        
        Args:
            ticker: Stock ticker symbol
            filing_type: Type of SEC filing to analyze (default: 10-K)
            
        Returns:
            Analysis results with recommendation
        """
        # Fetch SEC filing data
        print(f"[Charlie] Fetching {filing_type} data for {ticker}...")
        filing_data = fetch_filing_data(ticker, filing_type, count=1)
        
        if not filing_data.get("success"):
            return {
                "agent": self.name,
                "ticker": ticker,
                "persona": self.persona.value,
                "error": filing_data.get("error", "Failed to fetch filing data"),
                "analysis": None
            }
        
        # Prepare analysis prompt
        filings = filing_data.get("filings", [])
        if not filings:
            return {
                "agent": self.name,
                "ticker": ticker,
                "persona": self.persona.value,
                "error": f"No {filing_type} filings found for {ticker}",
                "analysis": None
            }
        
        latest_filing = filings[0]
        company_name = filing_data.get("company_name", ticker)
        
        prompt = f"""
Analyze {company_name} ({ticker}) from a fundamental perspective.

Available SEC Filing:
- Form: {latest_filing['form']}
- Filing Date: {latest_filing['filing_date']}
- Document URL: {latest_filing['document_url']}

Based on your expertise in fundamental analysis and your current risk persona, provide:

1. **Financial Health Assessment**: Evaluate the company's balance sheet strength, cash flow, and debt levels
2. **Economic Moat Analysis**: Assess competitive advantages and barriers to entry
3. **Management Quality**: Evaluate capital allocation and corporate governance
4. **Industry Position**: Analyze competitive positioning and market dynamics
5. **Key Risks**: Identify fundamental risks aligned with your risk persona
6. **Recommendation**: Provide your fundamental view (Bullish/Neutral/Bearish) with confidence level

Format your response as a structured analysis with clear sections.
"""
        
        # Generate analysis with fallback logic
        print(f"[Charlie] Analyzing {ticker} with {self.persona.value} persona...")
        
        try:
            response = self.model.generate_content(prompt)
            
            return {
                "agent": self.name,
                "role": self.role,
                "ticker": ticker,
                "persona": self.persona.value,
                "company_name": company_name,
                "filing_analyzed": {
                    "form": latest_filing['form'],
                    "filing_date": latest_filing['filing_date'],
                    "url": latest_filing['document_url']
                },
                "analysis": response.text,
                "timestamp": latest_filing.get("filing_date"),
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
        Get A2A Agent Card for Charlie by loading the agent.json file.
        """
        card_path = os.path.join(os.path.dirname(__file__), "agent.json")
        try:
            with open(card_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[Charlie] Error loading agent card: {e}")
            return {
                "name": "Charlie",
                "role": "Fundamental Analysis Specialist",
                "persona_support": ["zen", "alpha", "balanced"]
            }


def main():
    """Main entry point for testing Charlie agent."""
    parser = argparse.ArgumentParser(description="Charlie - Fundamental Analysis Agent")
    parser.add_argument("--ticker", type=str, required=True, help="Stock ticker symbol")
    parser.add_argument("--persona", type=str, default="zen", choices=["zen", "alpha"], help="Risk persona")
    parser.add_argument("--filing-type", type=str, default="10-K", choices=["10-K", "10-Q", "8-K"], help="SEC filing type")
    
    args = parser.parse_args()
    
    # Create agent with specified persona
    persona = RiskPersona.ZEN if args.persona == "zen" else RiskPersona.ALPHA
    charlie = CharlieAgent(persona=persona)
    
    # Perform analysis
    result = charlie.analyze(args.ticker, args.filing_type)
    
    # Print results
    print("\n" + "="*80)
    print(f"CHARLIE'S FUNDAMENTAL ANALYSIS - {args.ticker.upper()}")
    print(f"Persona: {persona.value.upper()}")
    print("="*80 + "\n")
    
    if result.get("error"):
        print(f"ERROR: {result['error']}")
    else:
        print(result["analysis"])
        print("\n" + "="*80)
        print(f"Filing Analyzed: {result['filing_analyzed']['form']} ({result['filing_analyzed']['filing_date']})")
        print("="*80)


if __name__ == "__main__":
    main()
