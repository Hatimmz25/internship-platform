from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.offer import InternshipOffer

router = APIRouter()


@router.get("")
def list_offers(
    country: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    query = db.query(InternshipOffer)
    if country:
        query = query.filter(InternshipOffer.country.ilike(f"%{country}%"))
    if search:
        query = query.filter(InternshipOffer.title.ilike(f"%{search}%"))
    return query.order_by(InternshipOffer.first_seen_at.desc()).limit(max(1, min(limit, 100))).all()


@router.get("/filters")
def get_filter_options(db: Session = Depends(get_db)):
    countries = db.query(InternshipOffer.country).distinct().all()
    return {
        "countries": [c[0] for c in countries if c[0]],
        "popular_skills": ["python", "pytorch", "sql", "tensorflow", "docker", "spark"],
    }