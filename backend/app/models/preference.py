"""
Subscriber Preference Model.
Stores configurable filter criteria for matching internship offers.
"""
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.core.db import Base


class AlertFrequency(str, Enum):
    INSTANT = "INSTANT"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    OFF = "OFF"


class Preference(Base):
    __tablename__ = "preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    preferred_countries = Column(JSON, default=list)
    preferred_cities = Column(JSON, default=list)
    workplace_types = Column(JSON, default=list)   # remote, hybrid, onsite
    internship_types = Column(JSON, default=list)  # pfe, standard
    target_roles = Column(JSON, default=list)
    skills = Column(JSON, default=list)
    preferred_languages = Column(JSON, default=list)
    keywords = Column(JSON, default=list)
    exclusion_keywords = Column(JSON, default=list)

    min_relevance_score = Column(Float, default=50.0)
    alert_frequency = Column(String(20), default=AlertFrequency.DAILY.value)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="preference")