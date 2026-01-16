"""
Simulation script for Autonomous Protocol Handshake Testing (A2A & AP2)
Executes a 3-round NVDA debate and verifies cryptographic signatures.
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from coordinator.server import DebateCoordinator
from coordinator.personas import RiskPersona
from judge.ap2_handler import AP2Handler
from judge.sigma_agent import SigmaAgent

def main():
    parser = argparse.ArgumentParser(description="Autonomous Protocol Handshake Simulator")
    parser.add_argument("--ticker", type=str, default="NVDA", help="Ticker to simulate")
    parser.add_argument("--persona", type=str, default="alpha", help="Risk persona (zen/alpha/balanced)")
    parser.add_argument("--rounds", type=int, default=3, help="Number of rounds")
    args = parser.parse_args()

    print(f"\n{'='*80}")
    print(f"PHASE 2: AUTONOMOUS PROTOCOL HANDSHAKE TEST - ${args.ticker}")
    print(f"{'='*80}\n")

    # 1. Initialize AP2 Handler and Create Mandate
    print("[STEP 1] Initializing AP2 Protocol & Creating Intent Mandate...")
    ap2 = AP2Handler()
    mandate = ap2.create_intent_mandate(
        user_id="antigravity_debugger",
        ticker=args.ticker,
        persona=args.persona
    )
    
    # Verify Mandate Signature
    if ap2.verify_mandate(mandate):
        print("✅ [AP2] Intent Mandate signature verified successfully.")
    else:
        print("❌ [AP2] Intent Mandate signature verification FAILED.")
        sys.exit(1)

    # 2. Run Debate
    print(f"\n[STEP 2] Orchestrating {args.rounds}-round A2A Debate...")
    
    # Map persona
    persona_map = {
        "zen": RiskPersona.ZEN,
        "alpha": RiskPersona.ALPHA,
        "balanced": RiskPersona.SIGMA
    }
    persona = persona_map.get(args.persona, RiskPersona.ALPHA)
    
    coordinator = DebateCoordinator(args.ticker, persona)
    
    # Simulate debate with some mock parameters for Gamma if needed
    # but coordinator/server.py already handles missing data if we configured it in Phase 1
    debate_result = coordinator.run_debate(
        rounds=args.rounds,
        gamma_price=145.0,  # Mock price for NVDA
        gamma_eps=1.80,    # Mock EPS
        gamma_growth_rate=45.0 # Mock Growth
    )
    
    log_file = debate_result["log_file"]
    print(f"\n✅ [A2A] Debate complete. Log saved to: {log_file}")

    # 3. Audit Round-Robin Structure
    print("\n[STEP 3] Auditing Round-Robin Structure & Grounding...")
    with open(log_file, 'r') as f:
        log_data = json.load(f)
    
    rounds = log_data.get("rounds", [])
    if len(rounds) != args.rounds:
        print(f"❌ [AUDIT] Expected {args.rounds} rounds, found {len(rounds)}.")
    else:
        print(f"✅ [AUDIT] Sequence length matches: {len(rounds)} rounds.")

    # Check for specialist grounding
    charlie_failed = False
    for i, r in enumerate(rounds):
        agents = r.get("agents", {})
        if "charlie" in agents:
            sources = agents["charlie"].get("grounding_sources", [])
            if not sources:
                print(f"⚠️ [AUDIT] Charlie missing grounding sources in Round {i+1}!")
                charlie_failed = True
            else:
                print(f"✅ [AUDIT] Charlie Round {i+1} grounded with: {', '.join(sources)}")
    
    # 4. Generate & Verify Alpha Packet
    print("\n[STEP 4] Synthesizing Alpha Packet (Trust Artifact)...")
    sigma = SigmaAgent()
    evaluation = sigma.evaluate_debate(log_file)
    
    alpha_packet = ap2.generate_alpha_packet(
        mandate=mandate,
        sigma_evaluation=evaluation,
        debate_log_path=log_file
    )
    
    print(f"Recommendation: {alpha_packet['recommendation']} ({alpha_packet['confidence']}%)")
    
    # Verify Alpha Packet Signature
    if ap2.verify_alpha_packet(alpha_packet):
        print("✅ [AP2] Alpha Packet signature verified successfully.")
    else:
        print("❌ [AP2] Alpha Packet signature verification FAILED.")
        sys.exit(1)

    packet_path = ap2.save_alpha_packet(alpha_packet)
    print(f"✅ [AP2] Trust Artifact saved: {packet_path}")

    print(f"\n{'='*80}")
    print("PHASE 2 TEST COMPLETE: A2A & AP2 PROTOCOLS SYNCHRONIZED")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
