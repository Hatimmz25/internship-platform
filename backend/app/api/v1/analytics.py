from collections import Counter
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.offer import InternshipOffer

router = APIRouter()

@router.get("/overview")
def get_analytics_overview(db: Session = Depends(get_db)):
    total = db.query(func.count(InternshipOffer.id)).scalar() or 0
    countries = (db.query(InternshipOffer.country, func.count(InternshipOffer.id))
                 .filter(InternshipOffer.country.isnot(None))
                 .group_by(InternshipOffer.country)
                 .order_by(func.count(InternshipOffer.id).desc()).limit(5).all())
    skills = Counter()
    for (s,) in db.query(InternshipOffer.required_skills).limit(5000):
        skills.update(s or [])
    return {"total_offers": total,
            "top_skills": [k for k, _ in skills.most_common(5)],
            "top_countries": [c for c, _ in countries]}