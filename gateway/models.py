"""
Database models for Authentication.
"""

from sqlalchemy import Boolean, Column, Integer, String
from gateway.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)  # admin, analyst, viewer
    is_active = Column(Boolean, default=True)


class ChatMessage(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    role = Column(String)
    message = Column(String)
    timestamp = Column(String) # Storing as ISO string for simplicity
