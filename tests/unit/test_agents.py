"""
Unit tests for Agents (Charlie, Delta, Gamma, Sigma).
"""

import pytest
from unittest.mock import MagicMock, patch
from agents.charlie_fundamental.agent import CharlieAgent
from agents.delta_sentiment.agent import DeltaAgent
from agents.gamma_valuation.agent import GammaAgent
from judge.sigma_agent import SigmaAgent
from coordinator.personas import RiskPersona

@pytest.fixture
def mock_genai_model():
    """Mock Gemini model response."""
    with patch("google.generativeai.GenerativeModel") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value.text = "Mocked Analysis Response"
        mock_cls.return_value = mock_instance
        yield mock_instance

class TestCharlieAgent:
    def test_analyze_success(self, mock_genai_model, mock_sec_filings):
        agent = CharlieAgent(persona=RiskPersona.ZEN)
        result = agent.analyze("AAPL")
        
        assert result["ticker"] == "AAPL"
        assert result["analysis"] == "Mocked Analysis Response"
        assert result["filing_analyzed"]["form"] == "10-K"
        assert "error" not in result

    def test_analyze_no_filings(self, mock_genai_model):
        # Patch where it is imported!
        with patch("agents.charlie_fundamental.agent.fetch_filing_data") as mock_fetch:
            mock_fetch.return_value = {"success": True, "filings": []}
            
            agent = CharlieAgent()
            result = agent.analyze("AAPL")
            
            assert "error" in result
            assert "No 10-K filings found" in result["error"]

class TestDeltaAgent:
    def test_analyze_success(self, mock_genai_model):
        # Patch where it is imported!
        with patch("agents.delta_sentiment.agent.get_news_stream") as mock_stream:
            mock_stream.return_value = {
                "success": True,
                "articles": [{"title": "Test"}],
                "count": 1,
                "time_range": "3 days"
            }
            
            agent = DeltaAgent(persona=RiskPersona.ALPHA)
            result = agent.analyze("TSLA", days=3)
            
            assert result["ticker"] == "TSLA"
            assert result["analysis"] == "Mocked Analysis Response"
            assert result["news_analyzed"]["article_count"] == 1

class TestGammaAgent:
    def test_analyze_success(self, mock_genai_model):
        agent = GammaAgent()
        result = agent.analyze(
            ticker="MSFT",
            price=300.0,
            eps=10.0,
            growth_rate=15.0
        )
        
        assert result["ticker"] == "MSFT"
        # Gamma calculates metrics locally before calling LLM
        assert "valuation_metrics" in result
        assert result["valuation_metrics"]["pe_ratio"] == 30.0

class TestSigmaAgent:
    def test_evaluate_debate(self, mock_genai_model):
        agent = SigmaAgent()
        
        # Mock debate log
        debate_log = {
            "debate_id": "test_debate",
            "ticker": "AAPL",
            "persona": "zen",
            "metadata": {"agents_participated": ["charlie", "delta"], "mcp_tools_used": ["fetch_filing_data"]},
            "rounds": [
                {
                    "round": 1,
                    "agents": {
                        "charlie": {
                            "analysis": "Buy because growth.",
                            "grounding_sources": ["10-K"]
                        },
                        "delta": {
                            "analysis": "Sell because bad news.", 
                            "grounding_sources": ["News"]
                        }
                    }
                },
                {
                    "round": 2,
                    "agents": {
                         "charlie": {"analysis": "Still Buy.", "grounding_sources": []}
                    }
                }
            ]
        }
        
        # We need to write this to a temp file because Sigma reads from file path
        import json
        with open("temp_debate_log.json", "w") as f:
            json.dump(debate_log, f)
            
        try:
            result = agent.evaluate_debate("temp_debate_log.json")
            
            assert result["debate_id"] == "test_debate"
            assert result["evaluation"]["faithfulness_score"] > 0
            assert result["evaluation"]["consistency_score"] > 0
            assert "final_recommendation" in result
            
        finally:
            import os
            if os.path.exists("temp_debate_log.json"):
                os.remove("temp_debate_log.json")

    def test_consistency_calculation(self):
        agent = SigmaAgent()
        # Mock log w/ flipping positions
        debate_log = {
            "rounds": [
                {"agents": {"charlie": {"analysis": "Buy strong growth"}}},
                {"agents": {"charlie": {"analysis": "Sell weak internals"}}}
            ]
        }
        score = agent.evaluate_consistency(debate_log)
        # Should be low/zero because of flip
        assert score < 100
