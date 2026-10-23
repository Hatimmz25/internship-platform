"""
Offer Match Model.
Stores structured match records between Subscribers and Internship Offers.
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.db import Base


class OfferMatch(Base):
    __tablename__ = "offer_matches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    offer_id = Column(Integer, ForeignKey("internship_offers.id", ondelete="CASCADE"), nullable=False, index=True)

    score = Column(Float, nullable=False, index=True)
    breakdown = Column(JSON, nullable=False, default=dict)
    reasons = Column(JSON, nullable=False, default=list)
    algorithm_version = Column(String(50), nullable=False, default="1.0.0-deterministic")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="matches")
    offer = relationship("InternshipOffer", backref="matches")
    notifications = relationship(
        "NotificationLog", back_populates="match", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("user_id", "offer_id", name="uq_user_offer_match"),
    )