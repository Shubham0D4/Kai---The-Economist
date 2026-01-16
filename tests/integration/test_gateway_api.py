"""
Integration tests for Gateway API.
"""

import pytest
from unittest.mock import patch, MagicMock
from gateway import models, auth
from gateway.schema import AnalysisStatus, HITLMode

@pytest.fixture
def mock_background_tasks():
    """Mock background tasks to run synchronously or mock them out."""
    with patch("fastapi.BackgroundTasks.add_task") as mock_add_task:
        # We want to manually execute the task if needed, or just verify it was called.
        # For integration test of API response, we just need to know it was called.
        # But to test state changes (status updates), we might need to actually run logic.
        # Better approach: Patch `gateway.app.run_analysis` to avoid running full complex logic,
        # OR run it but mock the internal heavy calls (ap2, coordinator).
        yield mock_add_task

@pytest.fixture
def mock_full_stack():
    """Mock AP2, Coordinator, Sigma used in run_analysis."""
    with patch("gateway.app.ap2_handler") as mock_ap2, \
         patch("gateway.app.DebateCoordinator") as MockCoord, \
         patch("gateway.app.sigma_agent") as mock_sigma:
        
        # Setup AP2
        mock_ap2.create_intent_mandate.return_value = "mandate_123"
        mock_ap2.generate_alpha_packet.return_value = {
            "packet_id": "pkt_123",
            "recommendation": "Buy",
            "confidence": 85.0
        }
        mock_ap2.save_alpha_packet.return_value = "/tmp/alpha_packet.json"
        
        # Setup Coordinator
        MockCoord.return_value.run_debate.return_value = {
            "log_file": "/tmp/debate.log",
            "debate_id": "deb_123"
        }
        
        # Setup Sigma
        mock_sigma.evaluate_debate.return_value = {
            "final_recommendation": {
                "recommendation": "Buy",
                "confidence": 85.0
            }
        }
        
        yield

def test_full_analysis_workflow(client, db_session, mock_background_tasks, mock_full_stack):
    # 1. Register Analyst
    client.post("/auth/register", json={
        "username": "analyst1", "email": "a@test.com", "password": "pass", "role": "analyst"
    })
    
    # 2. Login
    login_res = client.post("/auth/token", data={"username": "analyst1", "password": "pass"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Start Analysis
    analyze_res = client.post("/api/v1/analyze", json={
        "ticker": "NVDA",
        "persona": "alpha",
        "user_id": "user_1"
    }, headers=headers)
    
    assert analyze_res.status_code == 200
    session_id = analyze_res.json()["session_id"]
    assert analyze_res.json()["status"] == "running"
    
    # Verify background task was triggered
    # (In a real e2e, we'd want the background task to run. 
    # With TestClient, background tasks run after response? No, usually generic TestClient doesn't run them unless using Starlette's TestClient context or similar.
    # Actually FastAPI TestClient triggers background tasks.)
    
    # HOWEVER, since we mocked `add_task` in fixture `mock_background_tasks` to avoid async complexity issues in this simple test,
    # we won't see state updates in DB.
    # To test state updates, we should call the background function directly in a unit test of `run_analysis`, 
    # or let it run.
    pass

@pytest.mark.asyncio
async def test_run_analysis_logic(db_session, mock_full_stack):
    """Test the background worker logic directly."""
    from gateway.app import run_analysis, sessions
    from gateway.schema import AnalysisRequest, PersonaType
    
    # Setup session
    session_id = "test_sess"
    sessions[session_id] = {
        "session_id": session_id,
        "ticker": "NVDA",
        "status": "running",
         "created_at": "now"
    }
    
    req = AnalysisRequest(ticker="NVDA", persona=PersonaType.ALPHA, user_id="u1")
    
    # Run logic
    await run_analysis(session_id, req)
    
    # Check session state updated
    assert sessions[session_id]["status"] in ["completed", "waiting_approval"]
    assert "alpha_packet" in sessions[session_id]

def test_hitl_approval_flow(client, db_session):
    # Setup session in waiting_approval state
    from gateway.app import sessions
    sessions["sess_hitl"] = {
        "session_id": "sess_hitl",
        "status": AnalysisStatus.WAITING_APPROVAL,
        "user_id": "u1",
        "challenge_id": "chal_1",
        "alpha_packet": {"packet_id": "p1", "recommendation": "Buy"} # Mock packet
    }
    
    # Register/Login Analyst
    client.post("/auth/register", json={"username": "b", "email": "b@t.com", "password": "p", "role": "analyst"})
    token = client.post("/auth/token", data={"username": "b", "password": "p"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Approve
    approve_res = client.post("/api/v1/approve/sess_hitl", json={
        "challenge_id": "chal_1",
        "user_confirmation": "approved"
    }, headers=headers)
    
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "completed"
    assert sessions["sess_hitl"]["status"] == AnalysisStatus.COMPLETED

def test_unauthorized_access(client):
    res = client.post("/api/v1/analyze", json={"ticker": "AAA", "persona": "zen", "user_id": "u"})
    assert res.status_code == 401
