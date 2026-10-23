import logging
from typing import List, Literal, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.preference import Preference
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()
LIST_FIELDS = ["target_roles", "preferred_countries", "preferred_cities", "workplace_types",
               "internship_types", "skills", "preferred_languages", "keywords", "exclusion_keywords"]


class PreferenceUpdate(BaseModel):
    target_roles: Optional[List[str]] = None
    preferred_countries: Optional[List[str]] = None
    preferred_cities: Optional[List[str]] = None
    workplace_types: Optional[List[str]] = None
    internship_types: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    preferred_languages: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    exclusion_keywords: Optional[List[str]] = None
    alert_frequency: Optional[Literal["INSTANT", "DAILY", "WEEKLY", "OFF"]] = None
    min_relevance_score: Optional[float] = Field(None, ge=0, le=100)


def _get_or_create(db: Session, user: User) -> Preference:
    pref = db.query(Preference).filter_by(user_id=user.id).first()
    if not pref:
        pref = Preference(user_id=user.id)
        db.add(pref); db.commit(); db.refresh(pref)
    return pref


def _serialize(p: Preference) -> dict:
    d = {f: getattr(p, f) or [] for f in LIST_FIELDS}
    d.update(alert_frequency=p.alert_frequency, min_relevance_score=p.min_relevance_score)
    return d


@router.get("")
def get_preferences(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _serialize(_get_or_create(db, user))


@router.put("")
def update_preferences(payload: PreferenceUpdate, db: Session = Depends(get_db),
                       user: User = Depends(get_current_user)):
    pref = _get_or_create(db, user)
    for key, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(pref, key, value)
    db.commit()
    try:
        from app.tasks.matcher import rematch_subscriber_preferences_task
        rematch_subscriber_preferences_task.delay(user.id)
    except Exception as exc:  # broker down must not fail the save
        logger.warning("Could not queue rematch: %s", exc)
    return _serialize(pref)