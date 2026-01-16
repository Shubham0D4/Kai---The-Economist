"""
Unit tests for Gateway Authentication.
"""

import pytest
from unittest.mock import MagicMock
from gateway import auth, models, schema

def test_password_hashing():
    pwd = "secretpassword"
    hashed = auth.get_password_hash(pwd)
    assert hashed != pwd
    assert auth.verify_password(pwd, hashed)
    assert not auth.verify_password("wrongpassword", hashed)

def test_token_creation():
    data = {"sub": "testuser"}
    token = auth.create_access_token(data)
    assert isinstance(token, str)
    assert len(token) > 0

@pytest.mark.asyncio
async def test_get_current_user_valid(db_session):
    # Setup user
    user = models.User(username="validuser", hashed_password="hashed", role="analyst")
    db_session.add(user)
    db_session.commit()
    
    # Create token
    token = auth.create_access_token({"sub": "validuser"})
    
    # Call dependency
    user = await auth.get_current_user(token=token, db=db_session)
    assert user.username == "validuser"

@pytest.mark.asyncio
async def test_get_current_analyst_user():
    # Analyst user
    analyst = models.User(username="a", role="analyst", is_active=True)
    res = await auth.get_current_analyst_user(analyst)
    assert res == analyst
    
    # Viewer user (should fail)
    viewer = models.User(username="v", role="viewer", is_active=True)
    with pytest.raises(Exception) as excinfo:
        await auth.get_current_analyst_user(viewer)
    assert excinfo.value.status_code == 403
