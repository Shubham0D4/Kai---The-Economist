import unittest
import os
import sys
from coordinator.server import DebateCoordinator, RiskPersona
import pytest

import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class TestGovernanceReal(unittest.TestCase):
    def setUp(self):
        # Ensure API key is present
        if not os.getenv("GOOGLE_API_KEY"):
            self.skipTest("GOOGLE_API_KEY not found")
        # Wait to avoid Rate Limits (reset is usually 60s)
        print("\n[TEST] Sleeping 10s to respect Rate Limits...")
        time.sleep(10)

    def test_token_limit_enforcement(self):
        """
        Verify that the debate stops when the token limit is exceeded.
        We set a very low limit (e.g., 500) which should be hit immediately by the first agent.
        """
        print("\n[TEST] Testing Token Limit Enforcement...")
        ticker = "AAPL"
        coordinator = DebateCoordinator(ticker, RiskPersona.ZEN)
        
        # Set a very low limit to force early termination
        coordinator.TOKEN_LIMIT = 100 
        
        with self.assertRaises(Exception) as cm:
            coordinator.run_debate(rounds=1, charlie_filing_type="10-K", delta_days=3)
        
        self.assertIn("HARD LIMIT EXCEEDED", str(cm.exception))
        print(f"[TEST] SUCCESS: Caught expected exception: {cm.exception}")

    def test_circuit_breaker_execution(self):
        """
        Verify that the circuit breaker logic runs after Round 2.
        We can't easily force a low score without mocks, but we can verify
        that the check happens by inspecting stdout/logs (or just running it to ensure no crash).
        """
        print("\n[TEST] Testing Circuit Breaker Execution (Real API)...")
        ticker = "TSLA" # Volatile stock, good for debate
        coordinator = DebateCoordinator(ticker, RiskPersona.ALPHA)
        
        # Run 2 rounds
        # We need to provide dummy gamma params to skip Gamma or ensure it runs cheap
        # Let's skip Gamma by not providing params, to save tokens/time
        # But Circuit Breaker is after Round 2.
        
        try:
            result = coordinator.run_debate(
                rounds=2, 
                charlie_filing_type="10-K",
                delta_days=3
                # No Gamma params -> Gamma skipped
            )
            print("[TEST] Debate completed 2 rounds.")
            print(f"[TEST] Result status: {result.get('status', 'COMPLETED')}")
            
        except Exception as e:
            self.fail(f"Debate failed with error: {e}")

if __name__ == '__main__':
    unittest.main()
