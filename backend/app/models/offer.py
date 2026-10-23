"""
Internship Offer Model.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.db import Base


class InternshipOffer(Base):
    __tablename__ = "internship_offers"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("scraping_sources.id", ondelete="CASCADE"), nullable=False)
    source_item_id = Column(String(255), nullable=True)
    canonical_url = Column(String(1024), unique=True, index=True, nullable=False)
    fingerprint = Column(String(64), unique=True, index=True, nullable=False)

    title = Column(String(255), nullable=False)
    normalized_title = Column(String(255), index=True)
    company = Column(String(255), index=True, nullable=False)
    location_raw = Column(String(255))
    country = Column(String(100), index=True)
    workplace_type = Column(String(50))  # remote, hybrid, onsite
    internship_type = Column(String(50)) # pfe, standard
    description = Column(Text)
    required_skills = Column(JSON, default=list)
    languages = Column(JSON, default=list)

    published_at = Column(DateTime)
    application_deadline = Column(DateTime)
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    source = relationship("ScrapingSource", back_populates="offers")