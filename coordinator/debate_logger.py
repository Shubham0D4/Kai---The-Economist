"""
Debate Logger for Kai - Economist
Provides structured logging with grounding sources and formula traceability.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class DebateLogger:
    """
    Structured logger for agent debates with grounding source tracking.
    """
    
    def __init__(self, ticker: str, persona: str, log_dir: str = "debate_logs"):
        """
        Initialize debate logger.
        
        Args:
            ticker: Stock ticker being analyzed
            persona: Risk persona (zen/alpha)
            log_dir: Directory to save debate logs
        """
        self.ticker = ticker.upper()
        self.persona = persona
        self.log_dir = log_dir
        self.debate_id = f"{self.ticker}_{self.persona}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create log directory if it doesn't exist
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize debate structure
        self.debate_log = {
            "debate_id": self.debate_id,
            "ticker": self.ticker,
            "persona": self.persona,
            "start_time": datetime.now().isoformat(),
            "rounds": [],
            "metadata": {
                "total_rounds": 0,
                "agents_participated": [],
                "mcp_tools_used": [],
                "grounding_sources": []
            }
        }
    
    def _save_log(self):
        """Save the current log state to disk."""
        log_file = os.path.join(self.log_dir, f"{self.debate_id}.json")
        with open(log_file, 'w') as f:
            json.dump(self.debate_log, f, indent=2)
        self.log_file = log_file

    def log_system_message(self, message: str):
        """Log a system message for real-time feedback."""
        log_entry = {
            "agent": "system",
            "timestamp": datetime.now().isoformat(),
            "message": message
        }
        # Find latest round or add to a 'system' round? 
        # For simplicity, we can just add to the last round or the global metadata
        if self.debate_log["rounds"]:
            if "system_logs" not in self.debate_log["rounds"][-1]:
                self.debate_log["rounds"][-1]["system_logs"] = []
            self.debate_log["rounds"][-1]["system_logs"].append(log_entry)
        
        # Also print to console
        print(f"[SYSTEM] {message}")
        self._save_log()

    def log_round_start(self, round_number: int):
        """
        Log the start of a debate round.
        """
        round_data = {
            "round_number": round_number,
            "start_time": datetime.now().isoformat(),
            "agents": {},
            "system_logs": []
        }
        self.debate_log["rounds"].append(round_data)
        print(f"\n{'='*80}")
        print(f"ROUND {round_number} - {self.ticker} ({self.persona.upper()} PERSONA)")
        print(f"{'='*80}\n")
        self._save_log()
    
    def log_agent_response(
        self,
        round_number: int,
        agent_name: str,
        analysis: str,
        grounding_sources: List[str],
        mcp_tools_used: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log an agent's response in a debate round.
        
        Args:
            round_number: Round number
            agent_name: Name of the agent (charlie, delta, gamma)
            analysis: Agent's analysis text
            grounding_sources: List of data sources used (e.g., "10-K filing 2025-10-31")
            mcp_tools_used: List of MCP tools called (e.g., "fetch_filing_data")
            metadata: Additional metadata (formulas, parameters, etc.)
        """
        # Find the round
        round_idx = round_number - 1
        if round_idx >= len(self.debate_log["rounds"]):
            raise ValueError(f"Round {round_number} not started")
        
        # Add agent response
        agent_data = {
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis,
            "grounding_sources": grounding_sources,
            "mcp_tools_used": mcp_tools_used,
            "metadata": metadata or {}
        }
        
        self.debate_log["rounds"][round_idx]["agents"][agent_name] = agent_data
        
        # Update global metadata
        if agent_name not in self.debate_log["metadata"]["agents_participated"]:
            self.debate_log["metadata"]["agents_participated"].append(agent_name)
        
        for tool in mcp_tools_used:
            if tool not in self.debate_log["metadata"]["mcp_tools_used"]:
                self.debate_log["metadata"]["mcp_tools_used"].append(tool)
        
        for source in grounding_sources:
            if source not in self.debate_log["metadata"]["grounding_sources"]:
                self.debate_log["metadata"]["grounding_sources"].append(source)
        
        # Print to console
        print(f"[{agent_name.upper()}]")
        print(f"Grounding Sources: {', '.join(grounding_sources)}")
        print(f"MCP Tools: {', '.join(mcp_tools_used)}")
        print(f"\n{analysis}\n")
        print("-" * 80 + "\n")
        self._save_log()

    def log_agent_error(self, round_number: int, agent_name: str, error_message: str):
        """
        Log an agent error in a debate round.
        """
        round_idx = round_number - 1
        if round_idx >= len(self.debate_log["rounds"]):
            return
            
        error_entry = {
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "error": error_message,
            "status": "failed"
        }
        
        self.debate_log["rounds"][round_idx]["agents"][agent_name] = error_entry
        self.log_system_message(f"Error: {agent_name.capitalize()} failed - {error_message}")
        self._save_log()
    
    def log_formula(
        self,
        round_number: int,
        agent_name: str,
        formula_name: str,
        formula: str,
        parameters: Dict[str, Any],
        result: Any
    ):
        """
        Log a formula used by an agent (for traceability).
        
        Args:
            round_number: Round number
            agent_name: Name of the agent
            formula_name: Name of the formula (e.g., "DCF Valuation")
            formula: The actual formula as string
            parameters: Input parameters used
            result: Calculation result
        """
        round_idx = round_number - 1
        if round_idx >= len(self.debate_log["rounds"]):
            return
        
        if agent_name not in self.debate_log["rounds"][round_idx]["agents"]:
            return
        
        # Add formula to metadata
        if "formulas" not in self.debate_log["rounds"][round_idx]["agents"][agent_name]["metadata"]:
            self.debate_log["rounds"][round_idx]["agents"][agent_name]["metadata"]["formulas"] = []
        
        formula_data = {
            "name": formula_name,
            "formula": formula,
            "parameters": parameters,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        self.debate_log["rounds"][round_idx]["agents"][agent_name]["metadata"]["formulas"].append(formula_data)
        
        print(f"[FORMULA TRACED] {agent_name.upper()} - {formula_name}")
        print(f"Formula: {formula}")
        print(f"Parameters: {json.dumps(parameters, indent=2)}")
        print(f"Result: {result}\n")
        self._save_log()
    
    def log_cross_critique(
        self,
        round_number: int,
        critic_agent: str,
        target_agent: str,
        critique: str
    ):
        """
        Log a cross-critique between agents.
        
        Args:
            round_number: Round number
            critic_agent: Agent providing the critique
            target_agent: Agent being critiqued
            critique: The critique text
        """
        round_idx = round_number - 1
        if round_idx >= len(self.debate_log["rounds"]):
            return
        
        # Add cross-critique to round metadata
        if "cross_critiques" not in self.debate_log["rounds"][round_idx]:
            self.debate_log["rounds"][round_idx]["cross_critiques"] = []
        
        critique_data = {
            "critic": critic_agent,
            "target": target_agent,
            "critique": critique,
            "timestamp": datetime.now().isoformat()
        }
        
        self.debate_log["rounds"][round_idx]["cross_critiques"].append(critique_data)
        
        print(f"[CROSS-CRITIQUE] {critic_agent.upper()} → {target_agent.upper()}")
        print(f"{critique}\n")
        self._save_log()
    
    def finalize(self):
        """
        Finalize the debate log and save to file.
        """
        self.debate_log["end_time"] = datetime.now().isoformat()
        self.debate_log["metadata"]["total_rounds"] = len(self.debate_log["rounds"])
        
        # Calculate duration
        start = datetime.fromisoformat(self.debate_log["start_time"])
        end = datetime.fromisoformat(self.debate_log["end_time"])
        duration = (end - start).total_seconds()
        self.debate_log["metadata"]["duration_seconds"] = duration
        
        # Save to file
        log_file = os.path.join(self.log_dir, f"{self.debate_id}.json")
        with open(log_file, 'w') as f:
            json.dump(self.debate_log, f, indent=2)
        
        print(f"\n{'='*80}")
        print(f"DEBATE COMPLETE")
        print(f"{'='*80}")
        print(f"Debate ID: {self.debate_id}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Rounds: {self.debate_log['metadata']['total_rounds']}")
        print(f"Agents: {', '.join(self.debate_log['metadata']['agents_participated'])}")
        print(f"MCP Tools Used: {', '.join(self.debate_log['metadata']['mcp_tools_used'])}")
        print(f"Log saved to: {log_file}")
        print(f"{'='*80}\n")
        
        return log_file
    
    def get_round_context(self, round_number: int) -> Dict:
        """
        Get context from a specific round for passing to next round.
        
        Args:
            round_number: Round number to get context from
            
        Returns:
            Dictionary with agent responses from that round
        """
        round_idx = round_number - 1
        if round_idx >= len(self.debate_log["rounds"]):
            return {}
        
        return self.debate_log["rounds"][round_idx].get("agents", {})
    
    def get_debate_summary(self) -> Dict:
        """
        Get a summary of the debate so far.
        """
        return {
            "debate_id": self.debate_id,
            "ticker": self.ticker,
            "persona": self.persona,
            "rounds_completed": len(self.debate_log["rounds"]),
            "agents_participated": self.debate_log["metadata"]["agents_participated"],
            "mcp_tools_used": self.debate_log["metadata"]["mcp_tools_used"]
        }

    def get_logs(self) -> List[Dict]:
        """
        Get flat list of logs for the frontend, including system messages.
        """
        flat_logs = []
        for r in self.debate_log["rounds"]:
            # Add system logs for this round
            for sys_log in r.get("system_logs", []):
                flat_logs.append(sys_log)
                
            # Add agent responses
            for agent_name, response in r.get("agents", {}).items():
                if "error" in response:
                    flat_logs.append({
                        "timestamp": response["timestamp"],
                        "agent": "system",
                        "message": f"ERROR ({agent_name.capitalize()}): {response['error']}"
                    })
                else:
                    flat_logs.append({
                        "timestamp": response["timestamp"],
                        "agent": agent_name,
                        "message": response["analysis"]
                    })
                
            # Add cross critiques
            for critique in r.get("cross_critiques", []):
                flat_logs.append({
                    "timestamp": critique["timestamp"],
                    "agent": critique["critic"], # Now attributing to the critic agent
                    "message": f"Cross-Critique of {critique['target'].capitalize()}: {critique['critique']}"
                })
        return sorted(flat_logs, key=lambda x: x["timestamp"])


# For testing
if __name__ == "__main__":
    # Test the debate logger
    logger = DebateLogger("AAPL", "zen")
    
    # Round 1
    logger.log_round_start(1)
    logger.log_agent_response(
        round_number=1,
        agent_name="charlie",
        analysis="Apple shows strong fundamentals with solid cash flow...",
        grounding_sources=["10-K filing 2025-10-31"],
        mcp_tools_used=["fetch_filing_data"],
        metadata={"filing_type": "10-K"}
    )
    
    logger.log_agent_response(
        round_number=1,
        agent_name="gamma",
        analysis="PE ratio of 23.08 suggests fair valuation...",
        grounding_sources=["Current price data", "EPS calculation"],
        mcp_tools_used=["calculate_valuation_metrics"],
        metadata={"pe_ratio": 23.08}
    )
    
    logger.log_formula(
        round_number=1,
        agent_name="gamma",
        formula_name="PE Ratio",
        formula="PE = Price / EPS",
        parameters={"price": 150.0, "eps": 6.5},
        result=23.08
    )
    
    # Round 2
    logger.log_round_start(2)
    logger.log_cross_critique(
        round_number=2,
        critic_agent="delta",
        target_agent="charlie",
        critique="Charlie's fundamental analysis aligns with positive news sentiment..."
    )
    
    # Finalize
    log_file = logger.finalize()
    print(f"Test log saved to: {log_file}")
