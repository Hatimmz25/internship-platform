import logging
from celery import shared_task
from app.core.db import SessionLocal
from app.models.offer import InternshipOffer
from app.models.preference import Preference, AlertFrequency
from app.models.match import OfferMatch
from app.services.matcher import calculate_match_score

logger = logging.getLogger(__name__)


def _apply(db, offer, pref):
    """Create/update/remove the match for (user, offer). Returns (match, created)."""
    result = calculate_match_score(offer, pref)
    threshold = pref.min_relevance_score if pref.min_relevance_score is not None else 50.0
    qualifies = not result["is_excluded"] and result["score"] >= threshold
    existing = db.query(OfferMatch).filter_by(user_id=pref.user_id, offer_id=offer.id).first()

    if not qualifies:
        if existing and not existing.notifications:   # never delete already-notified matches
            db.delete(existing)
        return None, False
    if existing:
        existing.score = result["score"]
        existing.breakdown = result["breakdown"]
        existing.reasons = result["reasons"]
        existing.algorithm_version = result["algorithm_version"]
        return existing, False
    match = OfferMatch(user_id=pref.user_id, offer_id=offer.id, score=result["score"],
                       breakdown=result["breakdown"], reasons=result["reasons"],
                       algorithm_version=result["algorithm_version"])
    db.add(match)
    db.flush()
    return match, True


@shared_task(name="app.tasks.matcher.match_new_offer_task")
def match_new_offer_task(offer_id: int):
    from app.tasks.notifications import queue_match_notification_task
    db = SessionLocal()
    try:
        offer = db.get(InternshipOffer, offer_id)
        if not offer:
            return {"status": "error", "message": "Offer not found", "matches_created": 0}
        instant_ids, created = [], 0
        for pref in db.query(Preference).all():
            match, was_created = _apply(db, offer, pref)
            if was_created:
                created += 1
                if pref.alert_frequency == AlertFrequency.INSTANT.value:
                    instant_ids.append(match.id)
        db.commit()
        for match_id in instant_ids:          # queue only after commit
            queue_match_notification_task.delay(match_id)
        return {"offer_id": offer_id, "matches_created": created}
    finally:
        db.close()


@shared_task(name="app.tasks.matcher.rematch_subscriber_preferences_task")
def rematch_subscriber_preferences_task(user_id: int):
    db = SessionLocal()
    try:
        pref = db.query(Preference).filter_by(user_id=user_id).first()
        if not pref:
            return {"status": "error", "message": "No preferences"}
        for offer in db.query(InternshipOffer).all():
            _apply(db, offer, pref)
        db.commit()
        return {"status": "ok", "user_id": user_id}
    finally:
        db.close()