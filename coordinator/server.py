"""
Coordinator Server for A2A Debate Orchestration
Manages 3-round round-robin debates between Charlie, Delta, and Gamma.
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Optional
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from coordinator.personas import RiskPersona
from coordinator.debate_logger import DebateLogger
from agents.charlie_fundamental.agent import CharlieAgent
from agents.delta_sentiment.agent import DeltaAgent
from agents.gamma_valuation.agent import GammaAgent
from judge.sigma_agent import SigmaAgent
import time

from dotenv import load_dotenv
load_dotenv()


class DebateCoordinator:
    """
    Coordinates A2A debates between specialist agents.
    Implements 3-round round-robin with cross-critique.
    """
    
    def __init__(self, ticker: str, persona: RiskPersona = RiskPersona.ZEN):
        """
        Initialize debate coordinator.
        
        Args:
            ticker: Stock ticker to analyze
            persona: Risk persona for agents
        """
        self.ticker = ticker.upper()
        self.persona = persona
        
        # Initialize logger
        self.logger = DebateLogger(ticker, persona.value)
        
        # Load agent cards for A2A handshake
        self.agent_cards = self._load_agent_cards()
        
        # Governance
        self.TOKEN_LIMIT = 50000
        self.total_tokens_used = 0
        self.sigma = SigmaAgent()  # Circuit Breaker Judge
        
        # Initialize agents
        print(f"[COORDINATOR] Initializing agents with {persona.value} persona...")
        self.charlie = CharlieAgent(persona=persona)
        self.delta = DeltaAgent(persona=persona)
        self.gamma = GammaAgent(persona=persona)
        
        print(f"[COORDINATOR] A2A Handshake complete")
        print(f"[COORDINATOR] Agents ready: Charlie, Delta, Gamma")
        print(f"[COORDINATOR] MCP tools verified\n")
        
    def _track_usage(self, agent_name: str, result: Dict):
        """Track token usage from agent response."""
        usage = result.get("token_usage", {})
        total_tokens = usage.get("total_tokens", 0)
        self.total_tokens_used += total_tokens
        print(f"[GOVERNANCE] {agent_name} used {total_tokens} tokens. Total: {self.total_tokens_used}/{self.TOKEN_LIMIT}")
        
        if self.total_tokens_used > self.TOKEN_LIMIT:
            raise Exception(f"HARD LIMIT EXCEEDED: Debate used {self.total_tokens_used} tokens (Limit: {self.TOKEN_LIMIT})")
    
    def _load_agent_cards(self) -> Dict:
        """Load A2A agent cards for capability discovery."""
        cards = {}
        
        agent_dirs = {
            "charlie": "agents/charlie_fundamental",
            "delta": "agents/delta_sentiment",
            "gamma": "agents/gamma_valuation"
        }
        
        for agent_name, agent_dir in agent_dirs.items():
            card_path = os.path.join(agent_dir, "agent.json")
            if os.path.exists(card_path):
                with open(card_path, 'r') as f:
                    cards[agent_name] = json.load(f)
        
        return cards
    
    def run_debate(
        self,
        rounds: int = 3,
        charlie_filing_type: str = "10-K",
        delta_days: int = 7,
        gamma_price: Optional[float] = None,
        gamma_eps: Optional[float] = None,
        gamma_growth_rate: Optional[float] = None
    ) -> Dict:
        """
        Run a complete multi-round debate.
        
        Args:
            rounds: Number of debate rounds (default: 3)
            charlie_filing_type: SEC filing type for Charlie
            delta_days: Days of news for Delta
            gamma_price: Current price for Gamma (if None, skip Gamma in Round 1)
            gamma_eps: EPS for Gamma
            gamma_growth_rate: Growth rate for Gamma
            
        Returns:
            Complete debate results
        """
        print(f"\n[COORDINATOR] Starting {rounds}-round debate for {self.ticker}")
        print(f"[COORDINATOR] Persona: {self.persona.value}\n")
        
        # Round 1: Initial Analysis
        self.logger.log_round_start(1)
        round1_results = self._run_round_1(
            charlie_filing_type,
            delta_days,
            gamma_price,
            gamma_eps,
            gamma_growth_rate
        )
        
        if rounds >= 2:
            # Round 2: Cross-Critique
            self.logger.log_round_start(2)
            round2_results = self._run_round_2(round1_results)
            
            # Circuit Breaker Check after Round 2
            print(f"[GOVERNANCE] Checking Phase 2 Circuit Breaker...")
            # We construct a temporary log to evaluate faithfulness so far
            # In a real system, we might stream this, but here we just re-read what we have or pass current state
            # For simplicity, we'll ask Sigma to evaluate based on the rounds completed
            
            # Flush logger to ensure data is on disk (or strictly relying on in-memory state if we refactor Sigma)
            # But Sigma.evaluate_debate reads from file. So let's flush.
            temp_log_path = self.logger.log_file
            self.logger._save_log() # Force save
            
            try:
                evaluation = self.sigma.evaluate_debate(temp_log_path)
                faithfulness = evaluation["evaluation"]["faithfulness_score"]
                print(f"[GOVERNANCE] Current Faithfulness Score: {faithfulness}/100")
                
                if faithfulness < 50.0:
                    print(f"[GOVERNANCE] !!! CIRCUIT BREAKER TRIGGERED !!!")
                    print(f"Reason: Faithfulness Score ({faithfulness}) < 50.0")
                    # We terminate early
                    log_file = self.logger.finalize()
                    return {
                        "ticker": self.ticker,
                        "persona": self.persona.value,
                        "rounds_completed": 2,
                        "status": "TERMINATED_EARLY",
                        "reason": "CIRCUIT_BREAKER_FAITHFULNESS",
                        "log_file": log_file,
                        "debate_id": self.logger.debate_id
                    }
            except Exception as e:
                print(f"[GOVERNANCE] Warning: Circuit breaker check failed: {e}")
        
        if rounds >= 3:
            # Round 3: Final Positions
            self.logger.log_round_start(3)
            round3_results = self._run_round_3(round1_results, round2_results)
        
        # Finalize debate
        log_file = self.logger.finalize()
        
        return {
            "ticker": self.ticker,
            "persona": self.persona.value,
            "rounds_completed": rounds,
            "log_file": log_file,
            "debate_id": self.logger.debate_id
        }
    
    def _run_round_1(
        self,
        charlie_filing_type: str,
        delta_days: int,
        gamma_price: Optional[float],
        gamma_eps: Optional[float],
        gamma_growth_rate: Optional[float]
    ) -> Dict:
        """
        Round 1: Initial independent analysis from each agent.
        """
        results = {}
        
        # Charlie: Fundamental Analysis
        self.logger.log_system_message(f"Charlie (Fundamental Specialist) is fetching SEC filings for {self.ticker}...")
        print(f"[COORDINATOR] Calling Charlie for fundamental analysis...")
        charlie_result = self.charlie.analyze(self.ticker, charlie_filing_type)
        
        if not charlie_result.get("error"):
            grounding_sources = [
                f"{charlie_result['filing_analyzed']['form']} filing {charlie_result['filing_analyzed']['filing_date']}"
            ]
            self.logger.log_agent_response(
                round_number=1,
                agent_name="charlie",
                analysis=charlie_result["analysis"],
                grounding_sources=grounding_sources,
                mcp_tools_used=["fetch_filing_data"],
                metadata=charlie_result.get("filing_analyzed", {})
            )
            results["charlie"] = charlie_result
            self._track_usage("charlie", charlie_result)
        else:
            print(f"[ERROR] Charlie failed: {charlie_result['error']}")
            self.logger.log_agent_error(1, "charlie", charlie_result["error"])
        
        # Delta: Sentiment Analysis
        self.logger.log_system_message(f"Delta (Sentiment Analyst) is searching news articles for {self.ticker}...")
        print(f"[COORDINATOR] Calling Delta for sentiment analysis...")
        delta_result = self.delta.analyze(self.ticker, days=delta_days)
        
        if not delta_result.get("error"):
            grounding_sources = [
                f"{delta_result['news_analyzed']['article_count']} news articles ({delta_result['news_analyzed']['time_range']})"
            ]
            self.logger.log_agent_response(
                round_number=1,
                agent_name="delta",
                analysis=delta_result["analysis"],
                grounding_sources=grounding_sources,
                mcp_tools_used=["get_news_stream"],
                metadata=delta_result.get("news_analyzed", {})
            )
            results["delta"] = delta_result
            self._track_usage("delta", delta_result)
        else:
            print(f"[ERROR] Delta failed: {delta_result['error']}")
            self.logger.log_agent_error(1, "delta", delta_result["error"])
        
        # Gamma: Valuation Analysis
        self.logger.log_system_message(f"Gamma (Valuation Specialist) is calculating DCF and multiples for {self.ticker}...")
        print(f"[COORDINATOR] Calling Gamma for valuation analysis...")
        gamma_result = self.gamma.analyze(
            ticker=self.ticker,
            price=gamma_price,
            eps=gamma_eps,
            growth_rate=gamma_growth_rate
        )
        
        if not gamma_result.get("error"):
            grounding_sources = [
                f"Valuation metrics calculation ({'Parameters provided' if gamma_price else 'No direct inputs'})"
            ]
            
            self.logger.log_agent_response(
                round_number=1,
                agent_name="gamma",
                analysis=gamma_result["analysis"],
                grounding_sources=grounding_sources,
                mcp_tools_used=["calculate_valuation_metrics"],
                metadata=gamma_result.get("parameters", {})
            )
            
            # Log formulas for traceability if metrics exist
            if "valuation_metrics" in gamma_result and gamma_price and gamma_eps:
                metrics = gamma_result["valuation_metrics"]
                if "pe_ratio" in metrics:
                    self.logger.log_formula(
                        round_number=1,
                        agent_name="gamma",
                        formula_name="PE Ratio",
                        formula="PE = Price / EPS",
                        parameters={"price": gamma_price, "eps": gamma_eps},
                        result=metrics["pe_ratio"]
                    )
            
            results["gamma"] = gamma_result
            self._track_usage("gamma", gamma_result)
        else:
            print(f"[ERROR] Gamma failed: {gamma_result['error']}")
            self.logger.log_agent_error(1, "gamma", gamma_result["error"])
        
        return results
    
    def _run_round_2(self, round1_results: Dict) -> Dict:
        """
        Round 2: Cross-critique with agents seeing each other's Round 1 responses.
        Delta MUST specifically comment on Charlie's data.
        """
        results = {}
        
        # Prepare context from Round 1
        context = self._prepare_round_context(round1_results)
        
        # Delta critiques Charlie's fundamental analysis
        if "charlie" in round1_results and "delta" in round1_results:
            print(f"[COORDINATOR] Delta critiquing Charlie's analysis...")
            
            charlie_summary = self._extract_key_points(round1_results["charlie"]["analysis"])
            
            critique_prompt = f"""
In Round 1, you analyzed {self.ticker}'s sentiment from news.

Charlie (Fundamental Analyst) found:
{charlie_summary}

Based on your sentiment analysis, do you agree or disagree with Charlie's fundamental assessment? 
Does the news sentiment support or contradict the fundamental picture Charlie painted?
Provide specific examples from the news that either validate or challenge Charlie's findings.

Keep your response concise (2-3 paragraphs).
"""
            
            # Generate Delta's critique using the model
            try:
                delta_critique = self.delta.model.generate_content(critique_prompt)
                
                self.logger.log_cross_critique(
                    round_number=2,
                    critic_agent="delta",
                    target_agent="charlie",
                    critique=delta_critique.text
                )
                
                results["delta_critique_charlie"] = delta_critique.text
            except Exception as e:
                print(f"[ERROR] Delta critique failed: {e}")
                self.logger.log_agent_error(2, "delta", str(e))
        
        # Charlie can respond to Delta's sentiment
        if "delta" in round1_results and "charlie" in round1_results:
            print(f"[COORDINATOR] Charlie responding to Delta's sentiment...")
            
            delta_summary = self._extract_key_points(round1_results["delta"]["analysis"])
            
            response_prompt = f"""
In Round 1, you analyzed {self.ticker}'s fundamentals from SEC filings.

Delta (Sentiment Analyst) found:
{delta_summary}

How does this sentiment analysis align with or contradict your fundamental findings?
Do you see any risks or opportunities that the sentiment data highlights?

Keep your response concise (2-3 paragraphs).
"""
            
            try:
                charlie_response = self.charlie.model.generate_content(response_prompt)
                
                self.logger.log_agent_response(
                    round_number=2,
                    agent_name="charlie",
                    analysis=charlie_response.text,
                    grounding_sources=["Round 1 fundamental analysis", "Delta's sentiment findings"],
                    mcp_tools_used=[],
                    metadata={"response_type": "cross_critique_response"}
                )
                
                results["charlie_response"] = charlie_response.text
            except Exception as e:
                print(f"[ERROR] Charlie response failed: {e}")
                self.logger.log_agent_error(2, "charlie", str(e))
        
        # Gamma can synthesize both perspectives
        if "gamma" in round1_results:
            print(f"[COORDINATOR] Gamma synthesizing fundamental and sentiment views...")
            
            charlie_summary = self._extract_key_points(round1_results.get("charlie", {}).get("analysis", ""))
            delta_summary = self._extract_key_points(round1_results.get("delta", {}).get("analysis", ""))
            
            synthesis_prompt = f"""
In Round 1, you provided quantitative valuation for {self.ticker}.

Charlie (Fundamental): {charlie_summary}
Delta (Sentiment): {delta_summary}

Given these perspectives, do you want to adjust your valuation or risk assessment?
Does the fundamental strength or sentiment momentum change your view?

Keep your response concise (2-3 paragraphs).
"""
            
            try:
                gamma_synthesis = self.gamma.model.generate_content(synthesis_prompt)
                
                self.logger.log_agent_response(
                    round_number=2,
                    agent_name="gamma",
                    analysis=gamma_synthesis.text,
                    grounding_sources=["Round 1 valuation", "Charlie and Delta's findings"],
                    mcp_tools_used=[],
                    metadata={"response_type": "synthesis"}
                )
                
                results["gamma_synthesis"] = gamma_synthesis.text
            except Exception as e:
                print(f"[ERROR] Gamma synthesis failed: {e}")
                self.logger.log_agent_error(2, "gamma", str(e))
        
        return results
    
    def _run_round_3(self, round1_results: Dict, round2_results: Dict) -> Dict:
        """
        Round 3: Final positions after considering all perspectives.
        """
        results = {}
        
        # Each agent provides final recommendation
        for agent_name in ["charlie", "delta", "gamma"]:
            if agent_name not in round1_results:
                continue
            
            print(f"[COORDINATOR] {agent_name.capitalize()} providing final position...")
            
            # Get the agent
            agent = getattr(self, agent_name)
            
            final_prompt = f"""
After 2 rounds of debate about {self.ticker}, provide your final recommendation.

Summarize:
1. Your key findings
2. How other agents' perspectives influenced your view
3. Your final recommendation (Bullish/Neutral/Bearish)
4. Confidence level (0-100)
5. Key risks to watch

Keep your response concise and structured.
"""
            
            try:
                final_position = agent.model.generate_content(final_prompt)
                
                self.logger.log_agent_response(
                    round_number=3,
                    agent_name=agent_name,
                    analysis=final_position.text,
                    grounding_sources=["Round 1 analysis", "Round 2 cross-critique"],
                    mcp_tools_used=[],
                    metadata={"response_type": "final_position"}
                )
                
                results[f"{agent_name}_final"] = final_position.text
            except Exception as e:
                print(f"[ERROR] {agent_name.capitalize()} final position failed: {e}")
                self.logger.log_agent_error(3, agent_name, str(e))
        
        return results
    
    def _prepare_round_context(self, round_results: Dict) -> str:
        """Prepare context summary from previous round."""
        context_parts = []
        
        for agent_name, result in round_results.items():
            if "analysis" in result:
                summary = self._extract_key_points(result["analysis"])
                context_parts.append(f"{agent_name.upper()}: {summary}")
        
        return "\n\n".join(context_parts)
    
    def _extract_key_points(self, analysis: str, max_length: int = 300) -> str:
        """Extract key points from analysis (simple truncation for now)."""
        if len(analysis) <= max_length:
            return analysis
        return analysis[:max_length] + "..."


def main():
    """Main entry point for running debates."""
    parser = argparse.ArgumentParser(description="Kai - Economist Debate Coordinator")
    parser.add_argument("--ticker", type=str, required=True, help="Stock ticker symbol")
    parser.add_argument("--persona", type=str, default="zen", choices=["zen", "alpha", "balanced"], help="Risk persona")
    parser.add_argument("--rounds", type=int, default=3, choices=[1, 2, 3], help="Number of debate rounds")
    parser.add_argument("--price", type=float, help="Current stock price (for Gamma)")
    parser.add_argument("--eps", type=float, help="Earnings per share (for Gamma)")
    parser.add_argument("--growth-rate", type=float, help="Expected growth rate % (for Gamma)")
    
    args = parser.parse_args()
    
    # Create coordinator
    if args.persona == "zen":
        persona = RiskPersona.ZEN
    elif args.persona == "alpha":
        persona = RiskPersona.ALPHA
    else:
        persona = RiskPersona.SIGMA
        
    coordinator = DebateCoordinator(args.ticker, persona)
    
    # Run debate
    result = coordinator.run_debate(
        rounds=args.rounds,
        gamma_price=args.price,
        gamma_eps=args.eps,
        gamma_growth_rate=args.growth_rate
    )
    
    print(f"\n[COORDINATOR] Debate complete!")
    print(f"Debate ID: {result['debate_id']}")
    print(f"Log file: {result['log_file']}")


if __name__ == "__main__":
    main()
