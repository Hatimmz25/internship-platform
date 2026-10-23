import pytest
import os
from scrapy.http import HtmlResponse, Request
from internship_scraper.spiders.europa_jobs_spider import EuropaJobsRSSSpider

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

@pytest.fixture
def rss_fixture_response():
    file_path = os.path.join(FIXTURE_DIR, "europa_jobs_sample.xml")
    with open(file_path, "rb") as f:
        file_content = f.read()
    
    return HtmlResponse(
        url="https://ec.europa.eu/eures/eures-apps/rss/page/jobs?lang=en",
        body=file_content,
        encoding="utf-8",
        request=Request(url="https://ec.europa.eu/eures/eures-apps/rss/page/jobs?lang=en")
    )

def test_europa_rss_parsing(rss_fixture_response):
    spider = EuropaJobsRSSSpider()
    results = list(spider.parse(rss_fixture_response))

    assert len(results) > 0
    first_item = results[0]

    assert "canonical_url" in first_item
    assert "title" in first_item
    assert first_item["source_name"] == "europa_jobs_rss"
    assert isinstance(first_item["description"], str)