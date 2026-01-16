"""
AP2 (Agent Protocol v2) Handler
Manages intent mandates and cryptographically signed Alpha Packets.
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Optional, List
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import base64


class AP2Handler:
    """
    Handles AP2 protocol for intent mandates and signed Alpha Packets.
    Provides cryptographic verification for investment recommendations.
    """
    
    def __init__(self, private_key_path: Optional[str] = None):
        """
        Initialize AP2 handler.
        
        Args:
            private_key_path: Path to Ed25519 private key file (optional)
        """
        self.private_key_path = private_key_path or "ap2_private_key.pem"
        self.public_key_path = self.private_key_path.replace("private", "public")
        
        # Load or generate keys
        if os.path.exists(self.private_key_path):
            self.private_key, self.public_key = self._load_keys()
        else:
            self.private_key, self.public_key = self._generate_keys()
    
    def _generate_keys(self):
        """Generate new Ed25519 key pair."""
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        # Save keys
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        with open(self.private_key_path, 'wb') as f:
            f.write(private_pem)
        
        with open(self.public_key_path, 'wb') as f:
            f.write(public_pem)
        
        print(f"[AP2] Generated new key pair")
        print(f"[AP2] Private key: {self.private_key_path}")
        print(f"[AP2] Public key: {self.public_key_path}")
        
        return private_key, public_key
    
    def _load_keys(self):
        """Load existing Ed25519 key pair."""
        with open(self.private_key_path, 'rb') as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None
            )
        
        with open(self.public_key_path, 'rb') as f:
            public_key = serialization.load_pem_public_key(f.read())
        
        return private_key, public_key
    
    def create_intent_mandate(
        self,
        user_id: str,
        ticker: str,
        persona: str,
        authorization_text: Optional[str] = None
    ) -> Dict:
        """
        Create an intent mandate for user to sign before debate.
        
        Args:
            user_id: User identifier (wallet address, email, etc.)
            ticker: Stock ticker to analyze
            persona: Risk persona (zen/alpha)
            authorization_text: Custom authorization text
            
        Returns:
            Intent mandate dictionary
        """
        mandate_id = self._generate_id("mandate")
        timestamp = datetime.now().isoformat()
        
        if not authorization_text:
            authorization_text = f"I authorize Kai to analyze {ticker} with {persona} persona"
        
        mandate = {
            "mandate_id": mandate_id,
            "user_id": user_id,
            "ticker": ticker.upper(),
            "persona": persona,
            "timestamp": timestamp,
            "authorization": authorization_text,
            "version": "AP2-v1.0"
        }
        
        # Create signature payload
        payload = self._create_payload(mandate)
        
        # Sign with system key (in production, user would sign with their key)
        signature = self._sign(payload)
        mandate["signature"] = signature
        mandate["public_key"] = self._get_public_key_string()
        
        return mandate
    
    def verify_mandate(self, mandate: Dict) -> bool:
        """
        Verify an intent mandate signature.
        
        Args:
            mandate: Intent mandate dictionary
            
        Returns:
            True if signature is valid
        """
        signature = mandate.get("signature")
        if not signature:
            return False
        
        # Recreate payload
        mandate_copy = mandate.copy()
        mandate_copy.pop("signature", None)
        mandate_copy.pop("public_key", None)
        payload = self._create_payload(mandate_copy)
        
        # Verify signature
        return self._verify(payload, signature)
    
    def generate_alpha_packet(
        self,
        mandate: Dict,
        sigma_evaluation: Dict,
        debate_log_path: str
    ) -> Dict:
        """
        Generate a signed Alpha Packet after debate completion.
        
        Args:
            mandate: Original intent mandate
            sigma_evaluation: Sigma's evaluation results
            debate_log_path: Path to debate log file
            
        Returns:
            Signed Alpha Packet
        """
        packet_id = self._generate_id("packet")
        timestamp = datetime.now().isoformat()
        
        # Extract key information
        recommendation = sigma_evaluation["final_recommendation"]["recommendation"]
        confidence = sigma_evaluation["final_recommendation"]["confidence"]
        faithfulness = sigma_evaluation["evaluation"]["faithfulness_score"]
        consistency = sigma_evaluation["evaluation"]["consistency_score"]
        
        # Create debate summary
        debate_summary = self._create_debate_summary(sigma_evaluation)
        
        # Extract key risks from analysis
        analysis_text = sigma_evaluation["final_recommendation"]["analysis"]
        key_risks = self._extract_risks(analysis_text)
        
        alpha_packet = {
            "packet_id": packet_id,
            "mandate_id": mandate["mandate_id"],
            "ticker": sigma_evaluation["ticker"],
            "persona": sigma_evaluation["persona"],
            "recommendation": recommendation,
            "confidence": confidence,
            "quality_scores": {
                "faithfulness": faithfulness,
                "consistency": consistency,
                "overall": (faithfulness + consistency) / 2
            },
            "debate_summary": debate_summary,
            "key_risks": key_risks,
            "debate_log": debate_log_path,
            "timestamp": timestamp,
            "version": "AP2-v1.0"
        }
        
        # Create signature payload
        payload = self._create_payload(alpha_packet)
        
        # Sign the packet
        signature = self._sign(payload)
        alpha_packet["signature"] = signature
        alpha_packet["public_key"] = self._get_public_key_string()
        alpha_packet["verification_url"] = f"https://kai.verify/{packet_id}"
        
        return alpha_packet
    
    def verify_alpha_packet(self, alpha_packet: Dict) -> bool:
        """
        Verify an Alpha Packet signature.
        
        Args:
            alpha_packet: Alpha Packet dictionary
            
        Returns:
            True if signature is valid
        """
        signature = alpha_packet.get("signature")
        if not signature:
            return False
        
        # Recreate payload
        packet_copy = alpha_packet.copy()
        packet_copy.pop("signature", None)
        packet_copy.pop("public_key", None)
        packet_copy.pop("verification_url", None)
        payload = self._create_payload(packet_copy)
        
        # Verify signature
        return self._verify(payload, signature)
    
    def _generate_id(self, prefix: str) -> str:
        """Generate a unique ID."""
        timestamp = datetime.now().isoformat()
        hash_input = f"{prefix}_{timestamp}".encode()
        hash_output = hashlib.sha256(hash_input).hexdigest()
        return f"{prefix}_{hash_output[:16]}"
    
    def _create_payload(self, data: Dict) -> bytes:
        """Create a canonical payload for signing."""
        # Sort keys for deterministic serialization
        json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return json_str.encode('utf-8')
    
    def _sign(self, payload: bytes) -> str:
        """Sign a payload with private key."""
        signature = self.private_key.sign(payload)
        return base64.b64encode(signature).decode('utf-8')
    
    def _verify(self, payload: bytes, signature_b64: str) -> bool:
        """Verify a signature."""
        try:
            signature = base64.b64decode(signature_b64)
            self.public_key.verify(signature, payload)
            return True
        except Exception as e:
            print(f"[AP2] Verification failed: {e}")
            return False
    
    def _get_public_key_string(self) -> str:
        """Get public key as base64 string."""
        public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return base64.b64encode(public_pem).decode('utf-8')
    
    def _create_debate_summary(self, sigma_evaluation: Dict) -> Dict:
        """Create a concise debate summary."""
        return {
            "rounds": sigma_evaluation["metadata"]["rounds_evaluated"],
            "agents": sigma_evaluation["metadata"]["agents_evaluated"],
            "quality": sigma_evaluation["evaluation"]["overall_quality"]
        }
    
    def _extract_risks(self, analysis_text: str, max_risks: int = 3) -> List[str]:
        """Extract key risks from analysis text."""
        # Simple extraction - look for risk-related sentences
        risks = []
        
        # Split into sentences
        sentences = analysis_text.split('.')
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(word in sentence_lower for word in ['risk', 'concern', 'challenge', 'threat', 'caution']):
                risk = sentence.strip()
                if risk and len(risk) > 20:  # Meaningful risk
                    risks.append(risk)
                    if len(risks) >= max_risks:
                        break
        
        # Default risks if none found
        if not risks:
            risks = ["Market volatility", "Regulatory changes", "Economic uncertainty"]
        
        return risks[:max_risks]
    
    def save_alpha_packet(self, alpha_packet: Dict, output_dir: str = "alpha_packets") -> str:
        """
        Save Alpha Packet to file.
        
        Args:
            alpha_packet: Alpha Packet dictionary
            output_dir: Output directory
            
        Returns:
            Path to saved file
        """
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"{alpha_packet['packet_id']}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(alpha_packet, f, indent=2)
        
        print(f"[AP2] Alpha Packet saved to: {filepath}")
        return filepath


# For testing
if __name__ == "__main__":
    # Test AP2 handler
    handler = AP2Handler()
    
    # Create intent mandate
    print("\n=== CREATING INTENT MANDATE ===")
    mandate = handler.create_intent_mandate(
        user_id="user@example.com",
        ticker="AAPL",
        persona="zen"
    )
    print(json.dumps(mandate, indent=2))
    
    # Verify mandate
    print("\n=== VERIFYING MANDATE ===")
    is_valid = handler.verify_mandate(mandate)
    print(f"Mandate valid: {is_valid}")
    
    # Create mock Sigma evaluation
    mock_evaluation = {
        "ticker": "AAPL",
        "persona": "zen",
        "debate_id": "test_debate",
        "evaluation": {
            "faithfulness_score": 92.0,
            "consistency_score": 88.0,
            "overall_quality": 90.0
        },
        "final_recommendation": {
            "recommendation": "Buy",
            "confidence": 85.0,
            "analysis": "Strong fundamentals with key risk of regulatory pressure."
        },
        "metadata": {
            "rounds_evaluated": 3,
            "agents_evaluated": ["charlie", "delta", "gamma"]
        }
    }
    
    # Generate Alpha Packet
    print("\n=== GENERATING ALPHA PACKET ===")
    alpha_packet = handler.generate_alpha_packet(
        mandate=mandate,
        sigma_evaluation=mock_evaluation,
        debate_log_path="debate_logs/test.json"
    )
    print(json.dumps(alpha_packet, indent=2))
    
    # Verify Alpha Packet
    print("\n=== VERIFYING ALPHA PACKET ===")
    is_valid = handler.verify_alpha_packet(alpha_packet)
    print(f"Alpha Packet valid: {is_valid}")
    
    # Save Alpha Packet
    saved_path = handler.save_alpha_packet(alpha_packet)
    print(f"\nSaved to: {saved_path}")
