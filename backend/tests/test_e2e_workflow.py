import pytest
from unittest.mock import patch
from app.core.db import SessionLocal
from app.models.user import User, UserRole
from app.models.preference import Preference, AlertFrequency
from app.models.scraping import ScrapingSource
from app.models.offer import InternshipOffer
from app.models.match import OfferMatch
from app.models.notification import NotificationLog
from app.services.ingestion import process_and_upsert_offer
from app.tasks.matcher import match_new_offer_task
from app.tasks.notifications import queue_match_notification_task

@patch("app.tasks.notifications.get_email_provider")
def test_full_lifecycle_ingestion_to_notification(mock_get_provider):
    """
    E2E Scenario:
    1. Loads subscriber with saved preferences.
    2. Ingests a new synthetic PFE internship.
    3. Confirms offer is saved and relevance is calculated.
    4. Creates match and queues exactly one email notification.
    5. Re-ingests the same offer and confirms no duplicate alert.
    6. Tests an irrelevant offer and confirms it is ignored.
    """
    db = SessionLocal()
    
    try:
        # 1. Clean Database State
        db.query(NotificationLog).delete()
        db.query(OfferMatch).delete()
        db.query(InternshipOffer).filter(InternshipOffer.fingerprint.in_(["e2e_pfe_1", "e2e_irr_1"])).delete()
        db.query(Preference).delete()
        db.query(User).filter(User.email == "qa_e2e@example.com").delete()
        db.commit()

        # 2. Setup Subscriber & Preferences
        user = User(email="qa_e2e@example.com", hashed_password="hashed", role=UserRole.USER.value, is_active=True)
        db.add(user)
        db.commit()

        pref = Preference(
            user_id=user.id,
            target_roles=["data science", "ai"],
            skills=["python", "pytorch"],
            internship_types=["pfe"],
            min_relevance_score=60.0,
            alert_frequency=AlertFrequency.INSTANT.value
        )
        db.add(pref)
        
        source = db.query(ScrapingSource).first()
        if not source:
            source = ScrapingSource(name="E2E Source", slug="e2e", base_url="http://test.com")
            db.add(source)
            db.commit()

        # 3. Ingest Highly Relevant PFE Offer
        raw_match = {
            "source_item_id": "E2E-100",
            "canonical_url": "https://test.com/e2e-100",
            "fingerprint": "e2e_pfe_1",
            "title": "Data Science PFE Intern",
            "company": "AI Labs",
            "description": "Applying Deep Learning using Python and PyTorch.",
            "internship_type": "pfe",
            "required_skills": ["python", "pytorch"]
        }
        offer, is_new, _ = process_and_upsert_offer(db, source, raw_match)
        assert is_new is True

        # 4. Calculate Relevance & Create Match
        match_task_result = match_new_offer_task(offer.id)
        assert match_task_result["matches_created"] == 1
        
        match = db.query(OfferMatch).filter_by(offer_id=offer.id).first()
        assert match is not None
        assert match.score >= 60.0

        # 5. Queue Notification
        queue_match_notification_task(match.id)
        logs = db.query(NotificationLog).filter_by(match_id=match.id).all()
        assert len(logs) == 1
        assert logs[0].status == "SENT"
        assert mock_get_provider.return_value.send_email.call_count == 1

        # 6. Re-ingest Identical Offer (Idempotency Check)
        offer_dup, is_new_dup, _ = process_and_upsert_offer(db, source, raw_match)
        assert is_new_dup is False
        
        # Ensure attempting to notify again respects locks/logs
        queue_match_notification_task(match.id)
        logs_dup = db.query(NotificationLog).filter_by(match_id=match.id).all()
        assert len(logs_dup) == 1  # No duplicate log created
        assert mock_get_provider.return_value.send_email.call_count == 1 # Provider not called again

        # 7. Test Irrelevant Offer
        raw_irr = {
            "source_item_id": "E2E-101",
            "canonical_url": "https://test.com/e2e-101",
            "fingerprint": "e2e_irr_1",
            "title": "Marketing Summer Intern",
            "company": "Sales Corp",
            "description": "SEO and content strategy.",
            "internship_type": "summer",
            "required_skills": ["seo"]
        }
        offer_irr, is_new_irr, _ = process_and_upsert_offer(db, source, raw_irr)
        irr_task_result = match_new_offer_task(offer_irr.id)
        assert irr_task_result["matches_created"] == 0

    finally:
        # Teardown
        db.query(NotificationLog).delete()
        db.query(OfferMatch).delete()
        db.query(InternshipOffer).filter(InternshipOffer.fingerprint.in_(["e2e_pfe_1", "e2e_irr_1"])).delete()
        db.query(Preference).delete()
        db.query(User).filter(User.email == "qa_e2e@example.com").delete()
        db.commit()
        db.close()