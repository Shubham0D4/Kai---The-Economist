"""
Sigma - Final Decision Judge Agent
Evaluates debate quality and synthesizes final investment recommendation.
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Optional
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from coordinator.personas import get_sigma_system_instruction
from coordinator.llm_client import MultiLLMClient
from dotenv import load_dotenv

load_dotenv()


class SigmaAgent:
    """
    Sigma - Final Decision Judge
    
    Evaluates debate logs for faithfulness and consistency,
    then synthesizes final investment recommendation.
    """
    
    def __init__(self):
        """Initialize Sigma agent."""
        self.name = "Sigma"
        self.role = "Final Decision Judge"
        
        # Initialize hybrid model with Sigma system instruction
        system_instruction = get_sigma_system_instruction()
        self.model = MultiLLMClient(system_instruction=system_instruction)
    
    def evaluate_debate(self, debate_log_path: str) -> Dict:
        """
        Evaluate a completed debate and generate final recommendation.
        
        Args:
            debate_log_path: Path to debate log JSON file
            
        Returns:
            Evaluation results with scores and final recommendation
        """
        # Load debate log
        with open(debate_log_path, 'r') as f:
            debate_log = json.load(f)
        
        # Calculate scores
        faithfulness_score = self.evaluate_faithfulness(debate_log)
        consistency_score = self.evaluate_consistency(debate_log)
        
        # Synthesize final recommendation
        final_recommendation = self.synthesize_recommendation(
            debate_log,
            faithfulness_score,
            consistency_score
        )
        
        return {
            "agent": self.name,
            "debate_id": debate_log["debate_id"],
            "ticker": debate_log["ticker"],
            "persona": debate_log["persona"],
            "evaluation": {
                "faithfulness_score": faithfulness_score,
                "consistency_score": consistency_score,
                "overall_quality": (faithfulness_score + consistency_score) / 2
            },
            "final_recommendation": final_recommendation,
            "metadata": {
                "rounds_evaluated": len(debate_log["rounds"]),
                "agents_evaluated": debate_log["metadata"]["agents_participated"]
            }
        }
    
    def evaluate_faithfulness(self, debate_log: Dict) -> float:
        """
        Calculate faithfulness score (0-100).
        Measures how well claims are grounded in data sources.
        
        Args:
            debate_log: Complete debate log
            
        Returns:
            Faithfulness score (0-100)
        """
        total_responses = 0
        responses_with_sources = 0
        total_sources = 0
        
        for round_data in debate_log["rounds"]:
            for agent_name, agent_data in round_data.get("agents", {}).items():
                total_responses += 1
                
                grounding_sources = agent_data.get("grounding_sources", [])
                if grounding_sources:
                    responses_with_sources += 1
                    total_sources += len(grounding_sources)
        
        if total_responses == 0:
            return 0.0
        
        # Base score: percentage of responses with grounding sources
        base_score = (responses_with_sources / total_responses) * 100
        
        # Bonus for multiple sources per response (up to 10 points)
        avg_sources = total_sources / total_responses if total_responses > 0 else 0
        source_bonus = min(avg_sources * 3, 10)
        
        # Check for MCP tool usage
        mcp_tools_used = debate_log["metadata"].get("mcp_tools_used", [])
        tool_bonus = min(len(mcp_tools_used) * 2, 10)
        
        final_score = min(base_score + source_bonus + tool_bonus, 100)
        
        return round(final_score, 2)
    
    def evaluate_consistency(self, debate_log: Dict) -> float:
        """
        Calculate consistency score (0-100).
        Measures agent stability across rounds (penalizes flip-flopping).
        
        Args:
            debate_log: Complete debate log
            
        Returns:
            Consistency score (0-100)
        """
        if len(debate_log["rounds"]) < 2:
            return 100.0  # Can't flip-flop in one round
        
        # Track sentiment/position keywords across rounds
        agent_positions = {}
        
        for round_idx, round_data in enumerate(debate_log["rounds"]):
            for agent_name, agent_data in round_data.get("agents", {}).items():
                if agent_name not in agent_positions:
                    agent_positions[agent_name] = []
                
                analysis = agent_data.get("analysis", "").lower()
                
                # Simple sentiment detection
                bullish_words = ["bullish", "buy", "strong", "positive", "growth", "opportunity"]
                bearish_words = ["bearish", "sell", "weak", "negative", "decline", "risk"]
                
                bullish_count = sum(1 for word in bullish_words if word in analysis)
                bearish_count = sum(1 for word in bearish_words if word in analysis)
                
                if bullish_count > bearish_count:
                    position = "bullish"
                elif bearish_count > bullish_count:
                    position = "bearish"
                else:
                    position = "neutral"
                
                agent_positions[agent_name].append({
                    "round": round_idx + 1,
                    "position": position,
                    "bullish_count": bullish_count,
                    "bearish_count": bearish_count
                })
        
        # Calculate consistency for each agent
        consistency_scores = []
        
        for agent_name, positions in agent_positions.items():
            if len(positions) < 2:
                continue
            
            # Check for position changes
            changes = 0
            for i in range(1, len(positions)):
                if positions[i]["position"] != positions[i-1]["position"]:
                    changes += 1
            
            # Consistency = 100 - (changes / possible_changes * 100)
            possible_changes = len(positions) - 1
            agent_consistency = 100 - (changes / possible_changes * 100) if possible_changes > 0 else 100
            consistency_scores.append(agent_consistency)
        
        # Average consistency across all agents
        if not consistency_scores:
            return 100.0
        
        return round(sum(consistency_scores) / len(consistency_scores), 2)
    
    def synthesize_recommendation(
        self,
        debate_log: Dict,
        faithfulness_score: float,
        consistency_score: float
    ) -> Dict:
        """
        Synthesize final investment recommendation from debate.
        
        Args:
            debate_log: Complete debate log
            faithfulness_score: Calculated faithfulness score
            consistency_score: Calculated consistency score
            
        Returns:
            Final recommendation with confidence and reasoning
        """
        # Extract final positions from Round 3 (or last round)
        last_round = debate_log["rounds"][-1]
        agent_analyses = {}
        
        for agent_name, agent_data in last_round.get("agents", {}).items():
            agent_analyses[agent_name] = agent_data.get("analysis", "")
        
        # Prepare synthesis prompt
        ticker = debate_log["ticker"]
        persona = debate_log["persona"]
        
        analyses_text = "\n\n".join([
            f"**{agent.upper()}**:\n{analysis}"
            for agent, analysis in agent_analyses.items()
        ])
        
        prompt = f"""
You are evaluating a completed investment debate for {ticker} ({persona} persona).

DEBATE QUALITY SCORES:
- Faithfulness Score: {faithfulness_score}/100 (how well claims are grounded in data)
- Consistency Score: {consistency_score}/100 (agent stability across rounds)

FINAL AGENT POSITIONS:
{analyses_text}

Based on this debate, provide your final judgment:

1. **Final Recommendation**: Buy, Hold, or Sell
2. **Confidence Level**: 0-100 (consider debate quality scores)
3. **Key Supporting Evidence**: Top 3 points from the debate
4. **Key Risks**: Top 3 risks identified
5. **Consensus Assessment**: Did agents agree or disagree?
6. **Quality Assessment**: Comment on faithfulness and consistency scores

Format your response as structured sections.
"""
        
        # Generate synthesis
        response = self.model.generate_content(prompt)
        
        # Parse recommendation (simple extraction)
        analysis_text = response.text.lower()
        
        if "buy" in analysis_text and "sell" not in analysis_text:
            recommendation = "Buy"
        elif "sell" in analysis_text:
            recommendation = "Sell"
        else:
            recommendation = "Hold"
        
        # Estimate confidence based on scores and consensus
        base_confidence = (faithfulness_score + consistency_score) / 2
        
        return {
            "recommendation": recommendation,
            "confidence": round(base_confidence, 2),
            "analysis": response.text,
            "quality_metrics": {
                "faithfulness": faithfulness_score,
                "consistency": consistency_score
            }
        }
    
    def generate_report(self, evaluation: Dict) -> str:
        """
        Generate a formatted evaluation report.
        
        Args:
            evaluation: Evaluation results
            
        Returns:
            Formatted report string
        """
        report = f"""
{'='*80}
SIGMA'S FINAL EVALUATION - {evaluation['ticker']} ({evaluation['persona'].upper()})
{'='*80}

DEBATE QUALITY ASSESSMENT:
- Faithfulness Score: {evaluation['evaluation']['faithfulness_score']}/100
- Consistency Score: {evaluation['evaluation']['consistency_score']}/100
- Overall Quality: {evaluation['evaluation']['overall_quality']:.2f}/100

FINAL RECOMMENDATION:
- Decision: {evaluation['final_recommendation']['recommendation']}
- Confidence: {evaluation['final_recommendation']['confidence']:.2f}/100

{evaluation['final_recommendation']['analysis']}

{'='*80}
Debate ID: {evaluation['debate_id']}
Rounds Evaluated: {evaluation['metadata']['rounds_evaluated']}
Agents: {', '.join(evaluation['metadata']['agents_evaluated'])}
{'='*80}
"""
        return report


def main():
    """Main entry point for testing Sigma agent."""
    parser = argparse.ArgumentParser(description="Sigma - Final Decision Judge")
    parser.add_argument("--debate-log", type=str, required=True, help="Path to debate log JSON file")
    
    args = parser.parse_args()
    
    # Create Sigma agent
    sigma = SigmaAgent()
    
    # Evaluate debate
    evaluation = sigma.evaluate_debate(args.debate_log)
    
    # Print report
    report = sigma.generate_report(evaluation)
    print(report)
    
    # Save evaluation
    eval_file = args.debate_log.replace(".json", "_evaluation.json")
    with open(eval_file, 'w') as f:
        json.dump(evaluation, f, indent=2)
    
    print(f"\nEvaluation saved to: {eval_file}")


if __name__ == "__main__":
    main()
