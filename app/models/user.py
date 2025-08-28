"""
User model for Lumia application.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    """SQLAlchemy user model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Brain collection identifier
    collection_id = Column(String, unique=True, index=True)


class UserCreate(BaseModel):
    """Pydantic model for user creation."""
    email: EmailStr
    username: str
    password: str


class UserUpdate(BaseModel):
    """Pydantic model for user updates."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None


class UserResponse(BaseModel):
    """Pydantic model for user responses."""
    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime
    collection_id: str
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Pydantic model for user login."""
    email: str
    password: str


class Token(BaseModel):
    """Pydantic model for JWT tokens."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Pydantic model for token data."""
    email: Optional[str] = None 