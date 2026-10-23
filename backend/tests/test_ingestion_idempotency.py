from app.core.db import SessionLocal
from app.models.offer import InternshipOffer
from app.models.scraping import ScrapingSource
from app.services.ingestion import process_and_upsert_offer


def test_idempotent_ingestion():
    db = SessionLocal()
    try:
        # 1. Clean up any stale records from prior runs to ensure idempotent starting state
        db.query(InternshipOffer).filter(
            InternshipOffer.fingerprint == "test_fingerprint_hash_100"
        ).delete(synchronize_session=False)
        db.commit()

        source = db.query(ScrapingSource).first()
        if not source:
            source = ScrapingSource(
                name="Test Source",
                slug="test_source",
                base_url="https://test.com"
            )
            db.add(source)
            db.commit()

        raw_item = {
            "source_item_id": "TEST-100",
            "canonical_url": "https://test.com/job-100",
            "fingerprint": "test_fingerprint_hash_100",
            "title": "Data Engineering Intern PFE",
            "company": "Data Corp",
            "location_raw": "Berlin, Germany",
            "country": "Germany",
            "workplace_type": "remote",
            "internship_type": "pfe",
            "description": "SQL Python and Spark",
            "required_skills": ["python", "sql", "spark"],
        }

        # First Ingestion (New Offer)
        offer1, is_new1, updated1 = process_and_upsert_offer(db, source, raw_item)
        assert is_new1 is True

        # Second Ingestion (Duplicate Offer - Idempotency Check)
        offer2, is_new2, updated2 = process_and_upsert_offer(db, source, raw_item)
        assert is_new2 is False
        assert offer1.id == offer2.id

    finally:
        # Cleanup test offer after test execution
        db.query(InternshipOffer).filter(
            InternshipOffer.fingerprint == "test_fingerprint_hash_100"
        ).delete(synchronize_session=False)
        db.commit()
        db.close()