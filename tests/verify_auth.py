"""
Verification script for Authentication and Authorization.
"""

from fastapi.testclient import TestClient
from gateway.app import app
from gateway.database import Base, engine, SessionLocal
from gateway import models
import pytest

# Create test database
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_auth_flow():
    # 1. Access protected endpoint without token
    response = client.get("/api/v1/history?user_id=test")
    assert response.status_code == 401
    print("✅ Step 1: Protected endpoint rejects unauthenticated request")

    # 2. Register new user (Analyst)
    user_data = {
        "username": "analyst_user",
        "email": "analyst@example.com",
        "password": "securepassword",
        "role": "analyst"
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 200
    assert response.json()["username"] == "analyst_user"
    print("✅ Step 2: User registration successful")

    # 3. Login to get token
    login_data = {
        "username": "analyst_user",
        "password": "securepassword"
    }
    response = client.post("/auth/token", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Step 3: Login successful, token received")

    # 4. Access protected endpoint with token
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == "analyst_user"
    print("✅ Step 4: Protected endpoint accepts authenticated request")
    
    # 5. Test Role-Based Access Control (Viewer trying to Analyze)
    # Register Viewer
    viewer_data = {
        "username": "viewer_user",
        "email": "viewer@example.com",
        "password": "password123",
        "role": "viewer"
    }
    client.post("/auth/register", json=viewer_data)
    
    # Login Viewer
    response = client.post("/auth/token", data={"username": "viewer_user", "password": "password123"})
    viewer_token = response.json()["access_token"]
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}
    
    # Try to analyze (protected for Analyst+)
    # Note: We expect 403 Forbidden, request validation error or background task error might occur if we pass valid body
    # But first check auth
    analyze_request = {
        "ticker": "AAPL",
        "persona": "zen",
        "user_id": "viewer_user"
    }
    response = client.post("/api/v1/analyze", json=analyze_request, headers=viewer_headers)
    assert response.status_code == 403
    print("✅ Step 5: Viewer denied access to Analyst endpoint")

    print("\n🎉 All Auth Verification Tests Passed!")

if __name__ == "__main__":
    try:
        test_auth_flow()
    except AssertionError as e:
        print(f"❌ Test Failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
