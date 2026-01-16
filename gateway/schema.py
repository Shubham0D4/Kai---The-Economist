"""
Response Schemas for Gateway API
Pydantic models for standardized JSON responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class PersonaType(str, Enum):
    """Risk persona types."""
    ZEN = "zen"
    BALANCED = "balanced"
    ALPHA = "alpha"


class RecommendationType(str, Enum):
    """Investment recommendation types."""
    BUY = "Buy"
    HOLD = "Hold"
    SELL = "Sell"


class AnalysisStatus(str, Enum):
    """Analysis session status."""
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"


class HITLMode(str, Enum):
    """HITL mode types."""
    PASSIVE = "passive"
    ACTIVE = "active"


# Auth Models

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "viewer"  # admin, analyst, viewer


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


# Request Models

class AnalysisRequest(BaseModel):
    """Request to start new analysis."""
    ticker: str = Field(..., description="Stock ticker symbol", min_length=1, max_length=5)
    persona: PersonaType = Field(default=PersonaType.ZEN, description="Risk persona")
    user_id: str = Field(..., description="User identifier")
    price: Optional[float] = Field(None, description="Current stock price (optional)")
    eps: Optional[float] = Field(None, description="Earnings per share (optional)")
    growth_rate: Optional[float] = Field(None, description="Expected growth rate % (optional)")


class ApprovalRequest(BaseModel):
    """Request to approve step-up challenge."""
    challenge_id: str = Field(..., description="Challenge ID to approve")
    user_confirmation: str = Field(..., description="User confirmation (approved/rejected)")


class ChatRequest(BaseModel):
    """Chat request."""
    user_id: str = Field(..., description="User identifier")
    message: str = Field(..., description="User message")


class ChatResponse(BaseModel):
    """Chat response."""
    response: str = Field(..., description="AI response")
    timestamp: str = Field(..., description="Timestamp")


# Response Models

class QualityScores(BaseModel):
    """Debate quality scores."""
    faithfulness: float = Field(..., description="Faithfulness score (0-100)")
    consistency: float = Field(..., description="Consistency score (0-100)")
    overall: float = Field(..., description="Overall quality score (0-100)")


class DebateSummary(BaseModel):
    """Summary of debate execution."""
    rounds: int = Field(..., description="Number of rounds executed")
    agents: List[str] = Field(..., description="Agents that participated")
    quality: float = Field(..., description="Overall debate quality")


class AlphaPacket(BaseModel):
    """Signed Alpha Packet."""
    packet_id: str
    mandate_id: str
    ticker: str
    persona: str
    recommendation: RecommendationType
    confidence: float
    quality_scores: QualityScores
    debate_summary: DebateSummary
    key_risks: List[str]
    debate_log: str
    timestamp: str
    signature: str
    public_key: str
    verification_url: str
    version: str = "AP2-v1.0"


class Notification(BaseModel):
    """Passive mode notification."""
    type: str = Field(..., description="Notification type (info, warning, success)")
    message: str = Field(..., description="Notification message")
    recommendation: Optional[RecommendationType] = Field(None, description="Recommendation if available")
    confidence: Optional[float] = Field(None, description="Confidence level")


class StepUpChallenge(BaseModel):
    """Active mode step-up challenge."""
    challenge_id: str = Field(..., description="Unique challenge ID")
    message: str = Field(..., description="Challenge message for user")
    recommendation: RecommendationType = Field(..., description="Recommended action")
    confidence: float = Field(..., description="Confidence level (0-100)")
    requires_approval: bool = Field(True, description="Whether approval is required")
    expires_at: str = Field(..., description="Challenge expiration timestamp")
    key_points: List[str] = Field(default_factory=list, description="Key supporting points")


class AnalysisResponse(BaseModel):
    """Response from analysis request."""
    session_id: str = Field(..., description="Unique session ID")
    status: AnalysisStatus = Field(..., description="Current analysis status")
    hitl_mode: HITLMode = Field(..., description="HITL mode (passive/active)")
    ticker: str = Field(..., description="Stock ticker analyzed")
    persona: PersonaType = Field(..., description="Risk persona used")
    alpha_packet: Optional[AlphaPacket] = Field(None, description="Alpha Packet (if completed)")
    notification: Optional[Notification] = Field(None, description="Notification (passive mode)")
    step_up_challenge: Optional[StepUpChallenge] = Field(None, description="Step-up challenge (active mode)")
    created_at: str = Field(..., description="Session creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class StatusResponse(BaseModel):
    """Response from status check."""
    session_id: str
    status: AnalysisStatus
    hitl_mode: HITLMode
    ticker: str
    progress: Optional[str] = Field(None, description="Current progress message")
    alpha_packet: Optional[AlphaPacket] = None
    step_up_challenge: Optional[StepUpChallenge] = None
    debate_log: Optional[Dict[str, Any]] = Field(None, description="Structured debate logs")


class ApprovalResponse(BaseModel):
    """Response from approval/rejection."""
    session_id: str
    status: AnalysisStatus
    approval_status: str = Field(..., description="approved or rejected")
    alpha_packet: Optional[AlphaPacket] = None
    ready_for_execution: bool = Field(False, description="Whether ready for portfolio execution")
    message: str = Field(..., description="Response message")


class HistoryItem(BaseModel):
    """Historical analysis item."""
    session_id: str
    ticker: str
    persona: PersonaType
    recommendation: RecommendationType
    confidence: float
    created_at: str
    alpha_packet_id: str


class HistoryResponse(BaseModel):
    """Response from history request."""
    user_id: str
    analyses: List[HistoryItem]
    total_count: int


class ErrorResponse(BaseModel):
    """Error response."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    session_id: Optional[str] = Field(None, description="Session ID if applicable")


# For testing
if __name__ == "__main__":
    import json
    
    # Test schema creation
    request = AnalysisRequest(
        ticker="AAPL",
        persona=PersonaType.ZEN,
        user_id="test@example.com"
    )
    print("Analysis Request:")
    print(json.dumps(request.model_dump(), indent=2))
    
    # Test response
    response = AnalysisResponse(
        session_id="sess_123",
        status=AnalysisStatus.COMPLETED,
        hitl_mode=HITLMode.PASSIVE,
        ticker="AAPL",
        persona=PersonaType.ZEN,
        notification=Notification(
            type="info",
            message="Analysis complete. Recommendation: Hold",
            recommendation=RecommendationType.HOLD,
            confidence=65.0
        ),
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )
    print("\nAnalysis Response:")
    print(json.dumps(response.model_dump(), indent=2))
