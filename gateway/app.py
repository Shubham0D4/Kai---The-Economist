"""
Gateway API - FastAPI Application
Central API for iOS/Web clients with HITL workflow.
"""

import os
import sys
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from fastapi import FastAPI, HTTPException, BackgroundTasks, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from dotenv import load_dotenv
import yfinance as yf
import logging
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from gateway.schema import (
    AnalysisRequest, AnalysisResponse, StatusResponse,
    ApprovalRequest, ApprovalResponse, HistoryResponse, HistoryItem,
    ErrorResponse, AnalysisStatus, HITLMode, PersonaType,
    Token, UserCreate, UserResponse, ChatRequest, ChatResponse
)
from gateway.hitl_manager import HITLManager
from gateway import models, auth
from gateway.database import engine, get_db
from sqlalchemy.orm import Session
from coordinator.personas import RiskPersona
from coordinator.server import DebateCoordinator
from judge.sigma_agent import SigmaAgent
from judge.ap2_handler import AP2Handler
from groq import Groq

# Initialize Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Groq client
if os.getenv("GROQ_API_KEY"):
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
else:
    groq_client = None 

load_dotenv()

# Create tables
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Kai - Economist Gateway API",
    description="Central API for explainable investing copilot",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize managers
hitl_manager = HITLManager()
ap2_handler = AP2Handler()
sigma_agent = SigmaAgent()

# Session storage (in production, use Redis or database)
sessions: Dict[str, Dict] = {}
user_history: Dict[str, list] = {}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Kai - Economist Gateway API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.post("/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/auth/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/auth/me", response_model=UserResponse)
async def read_users_me(current_user: models.User = Depends(auth.get_current_active_user)):
    return current_user


@app.get("/api/v1/market/indices", tags=["Market Data"])
def get_market_indices(current_user: models.User = Depends(auth.get_current_active_user)):
    """Fetch live data for major indices."""
    indices = {
        "S&P 500": "^GSPC",
        "NASDAQ": "^IXIC",
        "DOW": "^DJI",
        "VIX": "^VIX"
    }
    
    results = []
    try:
        tickers = yf.Tickers(" ".join(indices.values()))
        for name, symbol in indices.items():
            ticker = tickers.tickers[symbol]
            # Fast info access
            info = ticker.fast_info
            price = info.last_price
            prev_close = info.previous_close
            change = price - prev_close
            change_percent = (change / prev_close) * 100
            
            results.append({
                "name": name,
                "value": f"{price:,.2f}",
                "change": f"{change_percent:+.2f}%",
                "positive": change >= 0
            })
    except Exception as e:
        logger.error(f"Error fetching indices: {e}")
        # Return fallback/mock if API fails to avoid breaking UI
        return [
            {"name": "S&P 500", "value": "4,783.45", "change": "+0.45%", "positive": True},
            {"name": "NASDAQ", "value": "15,055.65", "change": "+0.75%", "positive": True},
            {"name": "DOW", "value": "37,695.73", "change": "-0.12%", "positive": False},
        ]
        
    return results

@app.get("/api/v1/ticker/{symbol}/quote", tags=["Market Data"])
def get_ticker_quote(symbol: str, current_user: models.User = Depends(auth.get_current_active_user)):
    """Fetch real-time quote and stats for a ticker."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        fast_info = ticker.fast_info
        
        current_price = fast_info.last_price
        prev_close = fast_info.previous_close
        change = current_price - prev_close
        change_pct = (change / prev_close) * 100
        
        return {
            "symbol": symbol.upper(),
            "name": info.get('shortName', symbol),
            "price": f"{current_price:,.2f}",
            "change": f"{change_pct:+.2f}%",
            "is_positive": change >= 0,
            "market_cap": info.get('marketCap', 'N/A'),
            "pe_ratio": info.get('trailingPE', 'N/A'),
            "dividend_yield": f"{info.get('dividendYield', 0) * 100:.2f}%" if info.get('dividendYield') else "N/A",
            "high_52w": f"${info.get('fiftyTwoWeekHigh', 0):,.2f}",
            "low_52w": f"${info.get('fiftyTwoWeekLow', 0):,.2f}"
        }
    except Exception as e:
        logger.error(f"Error fetching quote for {symbol}: {e}")
        raise HTTPException(status_code=404, detail="Ticker not found")

@app.get("/api/v1/ticker/{symbol}/history", tags=["Market Data"])
def get_ticker_history(symbol: str, period: str = "1d", current_user: models.User = Depends(auth.get_current_active_user)):
    """Fetch historical data for charts. Periods: 1d, 5d, 1mo, ytd, 1y"""
    valid_periods = {"1d": "1m", "5d": "15m", "1mo": "60m", "ytd": "1d", "1y": "1d"}
    interval = valid_periods.get(period, "1d")
    
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        data = []
        for index, row in hist.iterrows():
            # Format time based on period
            if period in ["1d", "5d"]:
                time_label = index.strftime("%H:%M") if period == "1d" else index.strftime("%m-%d %H:%M")
            else:
                time_label = index.strftime("%Y-%m-%d")
                
            data.append({
                "name": time_label,
                "price": round(row['Close'], 2)
            })
            
        return data
    except Exception as e:
        logger.error(f"Error fetching history for {symbol}: {e}")
        return []



@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def analyze_ticker(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(auth.get_current_analyst_user)
):
    """
    Start new investment analysis.
    
    This endpoint:
    1. Creates intent mandate
    2. Runs 3-round debate
    3. Evaluates with Sigma
    4. Generates Alpha Packet
    5. Checks HITL requirement
    6. Returns response or waits for approval
    """
    try:
        # Create session
        session_id = f"sess_{uuid.uuid4().hex[:16]}"
        
        # Initialize session
        sessions[session_id] = {
            "session_id": session_id,
            "ticker": request.ticker.upper(),
            "persona": request.persona,
            "user_id": request.user_id,
            "status": AnalysisStatus.RUNNING,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Run analysis in background
        background_tasks.add_task(
            run_analysis,
            session_id,
            request
        )
        
        # Return initial response
        return AnalysisResponse(
            session_id=session_id,
            status=AnalysisStatus.RUNNING,
            hitl_mode=HITLMode.PASSIVE,  # Will be updated after analysis
            ticker=request.ticker.upper(),
            persona=request.persona,
            created_at=sessions[session_id]["created_at"],
            updated_at=sessions[session_id]["updated_at"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def run_analysis(session_id: str, request: AnalysisRequest):
    """
    Run complete analysis workflow (background task).
    """
    try:
        session = sessions[session_id]
        
        # Determine coordinator persona
        if request.persona == PersonaType.ZEN:
            coord_persona = RiskPersona.ZEN
        elif request.persona == PersonaType.BALANCED:
            coord_persona = RiskPersona.SIGMA
        else:
            coord_persona = RiskPersona.ALPHA
            
        # Initialize coordinator in background
        coordinator = DebateCoordinator(request.ticker, coord_persona)
        session["coordinator"] = coordinator
        
        # Log initialization
        coordinator.logger.log_system_message(f"Investment Mandate created for {request.ticker}. Analysis session {session_id} initialized.")
        
        # 1. Create intent mandate
        mandate = ap2_handler.create_intent_mandate(
            user_id=request.user_id,
            ticker=request.ticker,
            persona=request.persona.value
        )
        session["mandate"] = mandate
        
        # 2. Run debate (coordinator already initialized)
        debate_result = coordinator.run_debate(
            rounds=3,
            gamma_price=request.price,
            gamma_eps=request.eps,
            gamma_growth_rate=request.growth_rate
        )
        
        session["debate_log"] = debate_result["log_file"]
        
        # 3. Evaluate with Sigma
        evaluation = sigma_agent.evaluate_debate(debate_result["log_file"])
        session["evaluation"] = evaluation
        
        # 4. Generate Alpha Packet
        alpha_packet = ap2_handler.generate_alpha_packet(
            mandate=mandate,
            sigma_evaluation=evaluation,
            debate_log_path=debate_result["log_file"]
        )
        
        # Save Alpha Packet
        packet_path = ap2_handler.save_alpha_packet(alpha_packet)
        session["alpha_packet"] = alpha_packet
        session["alpha_packet_path"] = packet_path
        
        # 5. Check HITL requirement
        recommendation = evaluation["final_recommendation"]["recommendation"]
        confidence = evaluation["final_recommendation"]["confidence"]
        
        hitl_mode, reason = hitl_manager.evaluate_hitl_requirement(
            recommendation, confidence
        )
        
        session["hitl_mode"] = hitl_mode
        session["hitl_reason"] = reason
        
        # 6. Handle HITL mode
        if hitl_mode == HITLMode.PASSIVE:
            # Passive mode: Just notify
            notification = hitl_manager.create_notification(
                recommendation, confidence, request.ticker
            )
            session["notification"] = notification.model_dump()
            session["status"] = AnalysisStatus.COMPLETED
            
        else:
            # Active mode: Require approval
            challenge = hitl_manager.create_step_up_challenge(
                recommendation, confidence, request.ticker
            )
            session["step_up_challenge"] = challenge.model_dump()
            session["challenge_id"] = challenge.challenge_id
            session["status"] = AnalysisStatus.WAITING_APPROVAL
        
        session["updated_at"] = datetime.now().isoformat()
        
        # Add to user history
        if request.user_id not in user_history:
            user_history[request.user_id] = []
        
        user_history[request.user_id].append({
            "session_id": session_id,
            "ticker": request.ticker,
            "persona": request.persona,
            "recommendation": recommendation,
            "confidence": confidence,
            "created_at": session["created_at"],
            "alpha_packet_id": alpha_packet["packet_id"]
        })
        
    except Exception as e:
        session["status"] = AnalysisStatus.FAILED
        session["error"] = str(e)
        session["updated_at"] = datetime.now().isoformat()


@app.get("/api/v1/sessions/{session_id}/logs")
async def get_session_logs(session_id: str, current_user: models.User = Depends(auth.get_current_active_user)):
    """Get live debate logs for a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    # Priority 1: Get from in-memory coordinator for real-time
    coord = session.get("coordinator")
    if coord:
        return coord.logger.get_logs()
    
    # Priority 2: Get from saved log file (and flatten it)
    log_file = session.get("debate_log")
    if log_file and os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                debate_data = json.load(f)
                
                # Flatten structured log for frontend
                flat_logs = []
                for r in debate_data.get("rounds", []):
                    for sys_log in r.get("system_logs", []):
                        flat_logs.append(sys_log)
                    for agent_name, resp in r.get("agents", {}).items():
                        if "error" in resp:
                            flat_logs.append({
                                "timestamp": resp["timestamp"],
                                "agent": "system",
                                "message": f"ERROR ({agent_name.capitalize()}): {resp['error']}"
                            })
                        else:
                            flat_logs.append({
                                "timestamp": resp["timestamp"],
                                "agent": agent_name,
                                "message": resp["analysis"]
                            })
                return sorted(flat_logs, key=lambda x: x["timestamp"])
        except Exception as e:
            print(f"Error reading/flattening logs: {e}")
            
    return []


@app.get("/api/v1/status/{session_id}", response_model=StatusResponse)
async def get_status(session_id: str):
    """
    Check analysis status.
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    response = StatusResponse(
        session_id=session_id,
        status=session["status"],
        hitl_mode=session.get("hitl_mode", HITLMode.PASSIVE),
        ticker=session["ticker"],
        progress=session.get("progress")
    )
    
    # Add alpha packet if completed
    if session["status"] == AnalysisStatus.COMPLETED and "alpha_packet" in session:
        from gateway.schema import AlphaPacket, QualityScores, DebateSummary
        ap = session["alpha_packet"]
        response.alpha_packet = AlphaPacket(**ap)
    
    # Add step-up challenge if waiting approval
    if session["status"] == AnalysisStatus.WAITING_APPROVAL and "step_up_challenge" in session:
        from gateway.schema import StepUpChallenge
        response.step_up_challenge = StepUpChallenge(**session["step_up_challenge"])

    # Add debate logs if available
    if "debate_log" in session and os.path.exists(session["debate_log"]):
        try:
            import json
            with open(session["debate_log"], "r") as f:
                logs = json.load(f)
                response.debate_log = logs
        except Exception:
            pass  # Ignore log reading errors
    
    return response



@app.post("/api/v1/approve/{session_id}", response_model=ApprovalResponse)
async def approve_recommendation(
    session_id: str, 
    request: ApprovalRequest,
    current_user: models.User = Depends(auth.get_current_analyst_user)
):
    """
    Approve step-up challenge.
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    if session["status"] != AnalysisStatus.WAITING_APPROVAL:
        raise HTTPException(status_code=400, detail="Session not waiting for approval")
    
    # Approve challenge
    approved = hitl_manager.approve_challenge(request.challenge_id)
    
    if not approved:
        raise HTTPException(status_code=400, detail="Challenge approval failed")
    
    # Record decision
    hitl_manager.record_decision(
        session_id=session_id,
        challenge_id=request.challenge_id,
        decision="approved",
        user_id=session["user_id"]
    )
    
    # Update session
    session["status"] = AnalysisStatus.COMPLETED
    session["approval_status"] = "approved"
    session["approved_at"] = datetime.now().isoformat()
    session["updated_at"] = datetime.now().isoformat()
    
    # Get alpha packet
    from gateway.schema import AlphaPacket
    alpha_packet = AlphaPacket(**session["alpha_packet"])
    
    return ApprovalResponse(
        session_id=session_id,
        status=AnalysisStatus.COMPLETED,
        approval_status="approved",
        alpha_packet=alpha_packet,
        ready_for_execution=True,
        message="Recommendation approved. Ready for portfolio execution."
    )


@app.post("/api/v1/reject/{session_id}", response_model=ApprovalResponse)
async def reject_recommendation(
    session_id: str,
    current_user: models.User = Depends(auth.get_current_analyst_user)
):
    """
    Reject step-up challenge.
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    if session["status"] != AnalysisStatus.WAITING_APPROVAL:
        raise HTTPException(status_code=400, detail="Session not waiting for approval")
    
    challenge_id = session.get("challenge_id")
    if not challenge_id:
        raise HTTPException(status_code=400, detail="No challenge found")
    
    # Reject challenge
    rejected = hitl_manager.reject_challenge(challenge_id)
    
    if not rejected:
        raise HTTPException(status_code=400, detail="Challenge rejection failed")
    
    # Record decision
    hitl_manager.record_decision(
        session_id=session_id,
        challenge_id=challenge_id,
        decision="rejected",
        user_id=session["user_id"]
    )
    
    # Update session
    session["status"] = AnalysisStatus.REJECTED
    session["approval_status"] = "rejected"
    session["rejected_at"] = datetime.now().isoformat()
    session["updated_at"] = datetime.now().isoformat()
    
    return ApprovalResponse(
        session_id=session_id,
        status=AnalysisStatus.REJECTED,
        approval_status="rejected",
        ready_for_execution=False,
        message="Recommendation rejected by user."
    )


@app.get("/api/v1/history", response_model=HistoryResponse)
async def get_history(
    user_id: str,
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Get user's analysis history.
    """
    if user_id not in user_history:
        return HistoryResponse(
            user_id=user_id,
            analyses=[],
            total_count=0
        )
    
    history_items = [HistoryItem(**item) for item in user_history[user_id]]
    
    return HistoryResponse(
        user_id=user_id,
        analyses=history_items,
        total_count=len(history_items)
    )



@app.get("/api/v1/chat/history", response_model=List[ChatResponse])
async def get_chat_history(
    user_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Get chat history for a user.
    """
    try:
        history = db.query(models.ChatMessage).filter(
            models.ChatMessage.user_id == user_id
        ).order_by(models.ChatMessage.timestamp.asc()).limit(limit).all()
        
        return [
            ChatResponse(
                response=msg.message,
                timestamp=msg.timestamp,
                role=msg.role
            ) for msg in history
        ]
    except Exception as e:
        logger.error(f"Error fetching chat history: {e}")
        return []


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Chat with Market AI (Stateful via SQLite).
    """
    try:
        # 1. Save User Message
        user_msg = models.ChatMessage(
            user_id=request.user_id,
            role="user",
            message=request.message,
            timestamp=datetime.now().isoformat()
        )
        db.add(user_msg)
        db.commit()

        # 2. Get Context (Last 5 messages)
        history = db.query(models.ChatMessage).filter(
            models.ChatMessage.user_id == request.user_id
        ).order_by(models.ChatMessage.id.desc()).limit(5).all()
        
        # System Prompt setup
        messages = [{"role": "system", "content": "You are Kai, an advanced AI investment assistant. Be concise, professional, and data-driven."}]
        for msg in reversed(history):
            messages.append({"role": msg.role, "content": msg.message})
            
        # 3. Call Groq
        if not groq_client:
             # Mock response if API key missing
             ai_response = "I am currently in offline mode. Please configure my Groq API key."
        else:
            completion = groq_client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile",
            )
            ai_response = completion.choices[0].message.content

        # 4. Save AI Response
        ai_msg = models.ChatMessage(
            user_id=request.user_id,
            role="assistant",
            message=ai_response,
            timestamp=datetime.now().isoformat()
        )
        db.add(ai_msg)
        db.commit()

        return ChatResponse(response=ai_response, timestamp=ai_msg.timestamp, role="assistant")

    except Exception as e:
        print(f"Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("GATEWAY_HOST", "0.0.0.0")
    port = int(os.getenv("GATEWAY_PORT", 8080))
    
    print(f"Starting Kai - Economist Gateway API on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
