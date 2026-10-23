"""
Scraping models: sources and run history.
"""
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.db import Base


class RunStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class ScrapingSource(Base):
    __tablename__ = "scraping_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    base_url = Column(String(512), nullable=False)
    feed_url = Column(String(512), nullable=True)
    is_active = Column(Boolean, default=True)
    rate_limit_rps = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    offers = relationship("InternshipOffer", back_populates="source", cascade="all, delete-orphan")
    runs = relationship("ScrapingRun", back_populates="source", cascade="all, delete-orphan")


class ScrapingRun(Base):
    __tablename__ = "scraping_runs"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("scraping_sources.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default=RunStatus.PENDING.value)
    items_found = Column(Integer, default=0)
    items_new = Column(Integer, default=0)
    items_updated = Column(Integer, default=0)
    error_log = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    source = relationship("ScrapingSource", back_populates="runs")