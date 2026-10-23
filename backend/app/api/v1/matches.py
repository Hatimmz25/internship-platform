from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.match import OfferMatch
from app.models.user import User

router = APIRouter()

@router.get("")
def my_matches(limit: int = 50, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = (db.query(OfferMatch).filter(OfferMatch.user_id == user.id)
            .order_by(OfferMatch.score.desc()).limit(min(limit, 200)).all())
    return [{"id": m.id, "score": m.score, "reasons": m.reasons,
             "offer": {"id": m.offer.id, "title": m.offer.title, "company": m.offer.company,
                       "country": m.offer.country, "canonical_url": m.offer.canonical_url,
                       "internship_type": m.offer.internship_type}} for m in rows]