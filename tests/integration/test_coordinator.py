"""
Integration test for Debate Coordinator.
"""

import pytest
import os
from unittest.mock import MagicMock, patch
from coordinator.server import DebateCoordinator
from coordinator.personas import RiskPersona

@pytest.fixture
def mock_agents():
    """Mock all agent classes."""
    with patch("coordinator.server.CharlieAgent") as MockCharlie, \
         patch("coordinator.server.DeltaAgent") as MockDelta, \
         patch("coordinator.server.GammaAgent") as MockGamma:
        
        # Setup specific return values
        MockCharlie.return_value.analyze.return_value = {
            "analysis": "Charlie Analysis",
            "filing_analyzed": {"form": "10-K", "filing_date": "2023-01-01"}
        }
        MockDelta.return_value.analyze.return_value = {
            "analysis": "Delta Analysis",
            "news_analyzed": {"article_count": 5, "time_range": "7d"}
        }
        MockGamma.return_value.analyze.return_value = {
            "analysis": "Gamma Analysis",
            "parameters": {"pe": 20}
        }
        
        # Mock LLM usage in cross-critique (model.generate_content.text)
        mock_model = MagicMock()
        mock_model.generate_content.return_value.text = "Critique/Synthesis Text"
        MockCharlie.return_value.model = mock_model
        MockDelta.return_value.model = mock_model
        MockGamma.return_value.model = mock_model
        
        yield

def test_debate_flow(mock_agents):
    coordinator = DebateCoordinator("TEST", RiskPersona.ZEN)
    
    # Run 2-round debate
    result = coordinator.run_debate(
        rounds=2,
        gamma_price=100.0,
        gamma_eps=5.0,
        gamma_growth_rate=10.0
    )
    
    assert result["ticker"] == "TEST"
    assert result["rounds_completed"] == 2
    assert "log_file" in result
    
    # Verify file exists
    import os
    assert os.path.exists(result["log_file"])
    
    # Cleanup
    os.remove(result["log_file"])

def test_debate_single_round(mock_agents):
    coordinator = DebateCoordinator("TEST", RiskPersona.ALPHA)
    result = coordinator.run_debate(rounds=1)
    
    assert result["rounds_completed"] == 1
    # Check that gamma was skipped (no price provided)
    import json
    with open(result["log_file"]) as f:
        log = json.load(f)
        round1_agents = log["rounds"][0]["agents"]
        assert "charlie" in round1_agents
        assert "delta" in round1_agents
        assert "gamma" not in round1_agents
    
    os.remove(result["log_file"])
