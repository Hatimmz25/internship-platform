import json
from unittest.mock import patch

import pytest

from app.models.offer import InternshipOffer
from app.models.scraping import ScrapingSource
from app.tasks.scraping_tasks import scrape_source_task


@pytest.fixture
def mock_scrapy_results():
    return [{
        "source_item_id": "TEST-100",
        "canonical_url": "https://test.com/job-100",
        "fingerprint": "test_fingerprint_hash_100",
        "title": "Software Engineering Intern",
        "company": "Tech Corp",
        "required_skills": ["python", "docker"],
    }]


@patch("app.tasks.scraping_tasks.match_new_offer_task.delay")
@patch("subprocess.run")
def test_rediscovering_offer_prevents_duplicate_notifications(
    mock_subprocess_run, mock_match_delay, mock_scrapy_results, db_session
):
    """Scraping the same data twice must trigger the matcher only once.
    Needs Redis (the scrape lock), so run it inside docker compose."""

    source = ScrapingSource(name="Test Source", slug="test_source", base_url="https://test.com")
    db_session.add(source)
    db_session.commit()
    source_id = source.id

    def side_effect_run(*args, **kwargs):
        # Write the JSON file that Scrapy would have produced.
        output_file = args[0][args[0].index("-O") + 1]
        with open(output_file, "w") as f:
            json.dump(mock_scrapy_results, f)

        class CompletedProcessMock:
            returncode = 0
            stderr = ""

        return CompletedProcessMock()

    mock_subprocess_run.side_effect = side_effect_run

    # Run 1: offer is new
    result_run_1 = scrape_source_task(source_id)
    assert result_run_1["metrics"]["new"] == 1
    assert result_run_1["metrics"]["unchanged"] == 0
    assert mock_match_delay.call_count == 1

    # Run 2: identical data scraped again
    result_run_2 = scrape_source_task(source_id)
    assert result_run_2["metrics"]["new"] == 0
    assert result_run_2["metrics"]["unchanged"] == 1
    assert mock_match_delay.call_count == 1  # matcher NOT triggered again

    offers = db_session.query(InternshipOffer).filter_by(fingerprint="test_fingerprint_hash_100").all()
    assert len(offers) == 1