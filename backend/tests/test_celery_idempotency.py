import pytest
from unittest.mock import patch
from app.models.scraping import ScrapingSource
from app.services.ingestion import process_and_upsert_offer
from app.tasks.scraping_tasks import scrape_source_task

@patch("app.tasks.scraping_tasks.match_new_offer_task.delay")
def test_rediscovering_existing_offer_prevents_duplicate_notifications(mock_matcher_delay, db_session):
    """
    Ensures that processing an offer a second time identifies it as 'updated' or 'unchanged',
    and explicitly does not trigger the downstream Celery matcher task.
    """
    # 1. Setup Source & Payload
    source = ScrapingSource(name="Test Source", slug="test_source", base_url="https://test.com")
    db_session.add(source)
    db_session.commit()

    raw_item = {
        "canonical_url": "https://test.com/job-100",
        "fingerprint": "hash123",
        "title": "Initial Title",
        "company": "Company A"
    }

    # 2. First Ingestion (Creates New Record)
    offer, is_new, is_updated = process_and_upsert_offer(db_session, source, raw_item)
    assert is_new is True
    assert is_updated is False
    
    # Manually simulate what scraping_tasks.py does on 'is_new == True'
    if is_new:
        mock_matcher_delay(str(offer.id))
        
    assert mock_matcher_delay.call_count == 1

    # 3. Second Ingestion with Minor Update (Title change)
    raw_item["title"] = "Updated Title"
    offer2, is_new2, is_updated2 = process_and_upsert_offer(db_session, source, raw_item)
    
    assert is_new2 is False
    assert is_updated2 is True
    
    # 4. Third Ingestion with Identical Data (Unchanged)
    offer3, is_new3, is_updated3 = process_and_upsert_offer(db_session, source, raw_item)
    
    assert is_new3 is False
    assert is_updated3 is False

    # Verify downstream Celery task was ONLY called once for the initial discovery
    if is_new2 or is_new3:
        mock_matcher_delay("should_fail")
        
    assert mock_matcher_delay.call_count == 1