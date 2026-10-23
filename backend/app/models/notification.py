from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.db import Base


class NotificationLog(Base):
    __tablename__ = "notification_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    match_id = Column(Integer, ForeignKey("offer_matches.id", ondelete="CASCADE"), nullable=False, unique=True)
    channel = Column(String(50), default="email")
    status = Column(String(50), default="QUEUED", index=True)  # QUEUED / SENT / FAILED
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    match = relationship("OfferMatch", back_populates="notifications")