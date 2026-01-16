"""
Human-in-the-Loop (HITL) Manager
Manages passive notifications and active step-up challenges.
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from enum import Enum

# Import schemas
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from gateway.schema import (
    RecommendationType, HITLMode, Notification, StepUpChallenge
)


class HITLManager:
    """
    Manages Human-in-the-Loop workflow.
    Determines when to notify vs. when to require approval.
    """
    
    def __init__(
        self,
        strong_buy_threshold: float = 80.0,
        strong_sell_threshold: float = 80.0,
        low_confidence_threshold: float = 70.0,
        approval_timeout_minutes: int = 5
    ):
        """
        Initialize HITL manager.
        
        Args:
            strong_buy_threshold: Confidence threshold for strong buy
            strong_sell_threshold: Confidence threshold for strong sell
            low_confidence_threshold: Threshold below which is low confidence
            approval_timeout_minutes: Minutes before challenge expires
        """
        self.strong_buy_threshold = strong_buy_threshold
        self.strong_sell_threshold = strong_sell_threshold
        self.low_confidence_threshold = low_confidence_threshold
        self.approval_timeout_minutes = approval_timeout_minutes
        
        # Track pending approvals
        self.pending_approvals: Dict[str, Dict] = {}
    
    def evaluate_hitl_requirement(
        self,
        recommendation: str,
        confidence: float
    ) -> Tuple[HITLMode, str]:
        """
        Determine if HITL approval is required.
        
        Args:
            recommendation: Buy/Hold/Sell
            confidence: Confidence level (0-100)
            
        Returns:
            Tuple of (HITLMode, reason)
        """
        # Active Mode: Strong Buy or Strong Sell
        if recommendation == "Buy" and confidence >= self.strong_buy_threshold:
            return (HITLMode.ACTIVE, "Strong Buy signal requires approval")
        
        if recommendation == "Sell" and confidence >= self.strong_sell_threshold:
            return (HITLMode.ACTIVE, "Strong Sell signal requires approval")
        
        # Passive Mode: Hold or Low Confidence
        if recommendation == "Hold":
            return (HITLMode.PASSIVE, "Hold recommendation - notification only")
        
        if confidence < self.low_confidence_threshold:
            return (HITLMode.PASSIVE, "Low confidence - notification only")
        
        # Default: Passive for moderate confidence Buy/Sell
        return (HITLMode.PASSIVE, "Moderate confidence - notification only")
    
    def create_notification(
        self,
        recommendation: str,
        confidence: float,
        ticker: str
    ) -> Notification:
        """
        Create a passive mode notification.
        
        Args:
            recommendation: Buy/Hold/Sell
            confidence: Confidence level
            ticker: Stock ticker
            
        Returns:
            Notification object
        """
        # Determine notification type
        if confidence < self.low_confidence_threshold:
            notif_type = "warning"
            message = f"Analysis complete for {ticker}. Low confidence recommendation: {recommendation} ({confidence:.0f}%)"
        elif recommendation == "Hold":
            notif_type = "info"
            message = f"Analysis complete for {ticker}. Recommendation: {recommendation} ({confidence:.0f}%)"
        else:
            notif_type = "success"
            message = f"Analysis complete for {ticker}. Recommendation: {recommendation} ({confidence:.0f}%)"
        
        return Notification(
            type=notif_type,
            message=message,
            recommendation=RecommendationType(recommendation),
            confidence=confidence
        )
    
    def create_step_up_challenge(
        self,
        recommendation: str,
        confidence: float,
        ticker: str,
        key_points: Optional[list] = None
    ) -> StepUpChallenge:
        """
        Create an active mode step-up challenge.
        
        Args:
            recommendation: Buy/Sell
            confidence: Confidence level
            ticker: Stock ticker
            key_points: Key supporting points
            
        Returns:
            StepUpChallenge object
        """
        challenge_id = f"chal_{uuid.uuid4().hex[:16]}"
        
        # Create challenge message
        if recommendation == "Buy":
            message = f"🚀 Strong Buy signal detected for {ticker}! Tap to approve and proceed to execution."
        else:  # Sell
            message = f"⚠️ Strong Sell signal detected for {ticker}! Tap to approve and proceed to execution."
        
        # Calculate expiration
        expires_at = (datetime.now() + timedelta(minutes=self.approval_timeout_minutes)).isoformat()
        
        # Default key points if not provided
        if not key_points:
            key_points = [
                f"High confidence recommendation ({confidence:.0f}%)",
                "Based on multi-agent debate analysis",
                "Requires your approval to proceed"
            ]
        
        challenge = StepUpChallenge(
            challenge_id=challenge_id,
            message=message,
            recommendation=RecommendationType(recommendation),
            confidence=confidence,
            requires_approval=True,
            expires_at=expires_at,
            key_points=key_points
        )
        
        # Track pending approval
        self.pending_approvals[challenge_id] = {
            "challenge": challenge,
            "created_at": datetime.now(),
            "status": "pending"
        }
        
        return challenge
    
    def check_approval_status(self, challenge_id: str) -> Optional[str]:
        """
        Check if a challenge has been approved/rejected.
        
        Args:
            challenge_id: Challenge ID
            
        Returns:
            Status: "pending", "approved", "rejected", "expired", or None
        """
        if challenge_id not in self.pending_approvals:
            return None
        
        approval_data = self.pending_approvals[challenge_id]
        
        # Check if expired
        challenge = approval_data["challenge"]
        expires_at = datetime.fromisoformat(challenge.expires_at)
        if datetime.now() > expires_at:
            approval_data["status"] = "expired"
            return "expired"
        
        return approval_data["status"]
    
    def approve_challenge(self, challenge_id: str) -> bool:
        """
        Approve a step-up challenge.
        
        Args:
            challenge_id: Challenge ID
            
        Returns:
            True if approved successfully
        """
        if challenge_id not in self.pending_approvals:
            return False
        
        status = self.check_approval_status(challenge_id)
        if status != "pending":
            return False
        
        self.pending_approvals[challenge_id]["status"] = "approved"
        self.pending_approvals[challenge_id]["approved_at"] = datetime.now()
        
        return True
    
    def reject_challenge(self, challenge_id: str) -> bool:
        """
        Reject a step-up challenge.
        
        Args:
            challenge_id: Challenge ID
            
        Returns:
            True if rejected successfully
        """
        if challenge_id not in self.pending_approvals:
            return False
        
        status = self.check_approval_status(challenge_id)
        if status != "pending":
            return False
        
        self.pending_approvals[challenge_id]["status"] = "rejected"
        self.pending_approvals[challenge_id]["rejected_at"] = datetime.now()
        
        return True
    
    def record_decision(
        self,
        session_id: str,
        challenge_id: str,
        decision: str,
        user_id: str
    ) -> Dict:
        """
        Record user's approval/rejection decision.
        
        Args:
            session_id: Analysis session ID
            challenge_id: Challenge ID
            decision: "approved" or "rejected"
            user_id: User identifier
            
        Returns:
            Decision record
        """
        record = {
            "session_id": session_id,
            "challenge_id": challenge_id,
            "decision": decision,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # In production, save to database
        print(f"[HITL] Decision recorded: {decision} for challenge {challenge_id}")
        
        return record


# For testing
if __name__ == "__main__":
    import json
    
    # Test HITL manager
    hitl = HITLManager()
    
    print("=== TEST 1: Strong Buy (Active Mode) ===")
    mode, reason = hitl.evaluate_hitl_requirement("Buy", 85.0)
    print(f"Mode: {mode}, Reason: {reason}")
    
    if mode == HITLMode.ACTIVE:
        challenge = hitl.create_step_up_challenge("Buy", 85.0, "AAPL")
        print(json.dumps(challenge.model_dump(), indent=2))
        
        # Approve challenge
        approved = hitl.approve_challenge(challenge.challenge_id)
        print(f"Approved: {approved}")
        status = hitl.check_approval_status(challenge.challenge_id)
        print(f"Status: {status}")
    
    print("\n=== TEST 2: Hold (Passive Mode) ===")
    mode, reason = hitl.evaluate_hitl_requirement("Hold", 65.0)
    print(f"Mode: {mode}, Reason: {reason}")
    
    if mode == HITLMode.PASSIVE:
        notification = hitl.create_notification("Hold", 65.0, "AAPL")
        print(json.dumps(notification.model_dump(), indent=2))
    
    print("\n=== TEST 3: Low Confidence Buy (Passive Mode) ===")
    mode, reason = hitl.evaluate_hitl_requirement("Buy", 55.0)
    print(f"Mode: {mode}, Reason: {reason}")
    
    if mode == HITLMode.PASSIVE:
        notification = hitl.create_notification("Buy", 55.0, "AAPL")
        print(json.dumps(notification.model_dump(), indent=2))
