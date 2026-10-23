import ipaddress
from datetime import datetime, timedelta
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_admin
from app.core.db import get_db
from app.models.notification import NotificationLog
from app.models.offer import InternshipOffer
from app.models.scraping import ScrapingRun, ScrapingSource
from app.models.user import User
from app.tasks.scraping_tasks import scrape_source_task

router = APIRouter(dependencies=[Depends(get_current_admin)])


def validate_safe_url(url: str):
    """Prevents administrators from configuring internal network scanning."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("URL must use HTTP or HTTPS.")

    host = parsed.hostname
    if not host:
        raise ValueError("URL must include a host name.")

    forbidden_hosts = {"localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254", "::1"}
    if host in forbidden_hosts or host.endswith((".local", ".localhost", ".internal")):
        raise ValueError("Configuring internal or private network URLs is strictly prohibited.")

    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None  # a normal domain name
    if ip and (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast):
        raise ValueError("Configuring internal or private network URLs is strictly prohibited.")


class SourceUpdate(BaseModel):
    is_active: bool
    rate_limit_rps: float = Field(gt=0, le=10)
    base_url: str


@router.get("/kpis")
def get_dashboard_kpis(db: Session = Depends(get_db)):
    """Calculates real-time, database-backed platform KPIs."""
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    return {
        "total_active_offers": db.query(InternshipOffer).count(),
        "recent_offers_7d": db.query(InternshipOffer)
        .filter(InternshipOffer.first_seen_at >= seven_days_ago)
        .count(),
        "active_subscribers": db.query(User)
        .filter(User.is_active == True, User.role.in_(["USER", "SUBSCRIBER"]))  # noqa: E712
        .count(),
        "active_sources": db.query(ScrapingSource).filter(ScrapingSource.is_active == True).count(),  # noqa: E712
        "pending_notifications": db.query(NotificationLog).filter(NotificationLog.status == "QUEUED").count(),
        "failed_notifications": db.query(NotificationLog).filter(NotificationLog.status == "FAILED").count(),
    }


@router.get("/analytics")
def get_platform_analytics(db: Session = Depends(get_db)):
    """Builds chart payloads from exact database aggregations."""
    countries = (
        db.query(InternshipOffer.country, func.count(InternshipOffer.id))
        .group_by(InternshipOffer.country)
        .all()
    )
    notifications = (
        db.query(NotificationLog.status, func.count(NotificationLog.id))
        .group_by(NotificationLog.status)
        .all()
    )
    types = (
        db.query(InternshipOffer.internship_type, func.count(InternshipOffer.id))
        .group_by(InternshipOffer.internship_type)
        .all()
    )

    return {
        "offers_by_country": [{"name": c[0], "value": c[1]} for c in countries if c[0]],
        "notification_rates": [{"name": n[0], "value": n[1]} for n in notifications if n[0]],
        "offers_by_type": [{"name": t[0], "value": t[1]} for t in types if t[0]],
    }


@router.get("/sources")
def list_managed_sources(db: Session = Depends(get_db)):
    sources = db.query(ScrapingSource).order_by(ScrapingSource.name).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "slug": s.slug,
            "base_url": s.base_url,
            "is_active": s.is_active,
            "rate_limit_rps": s.rate_limit_rps,
            "created_at": s.created_at,
        }
        for s in sources
    ]


@router.put("/sources/{source_id}")
def update_source_config(source_id: int, payload: SourceUpdate, db: Session = Depends(get_db)):
    source = db.get(ScrapingSource, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    try:
        validate_safe_url(payload.base_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    source.is_active = payload.is_active
    source.rate_limit_rps = payload.rate_limit_rps
    source.base_url = payload.base_url
    db.commit()
    return {"message": "Source updated successfully"}


@router.post("/sources/{source_id}/trigger")
def trigger_manual_scrape(source_id: int, db: Session = Depends(get_db)):
    """Allows admins to inject an out-of-band scraping task immediately."""
    if not db.get(ScrapingSource, source_id):
        raise HTTPException(status_code=404, detail="Source not found")
    task = scrape_source_task.delay(source_id)
    return {"message": "Scrape queued", "task_id": str(task.id)}


@router.get("/runs")
def list_scraping_runs(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 200))
    runs = (
        db.query(ScrapingRun)
        .options(joinedload(ScrapingRun.source))
        .order_by(ScrapingRun.started_at.desc())
        .offset(max(0, offset))
        .limit(limit)
        .all()
    )
    return [
        {
            "id": run.id,
            "source_name": run.source.name,
            "status": run.status,
            "items_found": run.items_found,
            "items_new": run.items_new,
            "started_at": run.started_at,
            "finished_at": run.finished_at,
            "duration_seconds": (run.finished_at - run.started_at).total_seconds()
            if run.finished_at and run.started_at
            else None,
            "error_log": run.error_log,
        }
        for run in runs
    ]