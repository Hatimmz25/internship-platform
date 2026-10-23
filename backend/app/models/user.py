"""
User ORM Model.
"""
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.core.db import Base


class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    SUBSCRIBER = "SUBSCRIBER"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.USER.value)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    preference = relationship("Preference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    matches = relationship("OfferMatch", back_populates="user", cascade="all, delete-orphan")