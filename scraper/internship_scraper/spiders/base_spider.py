import scrapy
from typing import Dict, Any, Generator
from datetime import datetime
from bs4 import BeautifulSoup


class BaseInternshipSpider(scrapy.Spider):
    """
    Base Spider enforcing compliance, logging, and unified text parsing methods.
    """
    
    custom_settings: Dict[str, Any] = {
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'DOWNLOAD_DELAY': 2.0,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 2.0,
        'AUTOTHROTTLE_MAX_DELAY': 10.0,
        'HTTPCACHE_ENABLED': False,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stats_summary = {
            "source": self.name,
            "start_time": datetime.utcnow().isoformat(),
            "items_scraped": 0,
            "errors": 0
        }

    def parse(self, response: scrapy.http.Response) -> Generator[Dict[str, Any], None, None]:
        raise NotImplementedError("Subclasses must implement parse()")

    def clean_html(self, raw_html: str) -> str:
        if not raw_html:
            return ""
        soup = BeautifulSoup(raw_html, "html.parser")
        for element in soup(["script", "style", "iframe"]):
            element.decompose()
        return soup.get_text(separator=" ", strip=True)

    def parse_workplace_type(self, text: str) -> str:
        text_lower = text.lower()
        if "remote" in text_lower or "teletravail" in text_lower:
            return "remote"
        elif "hybrid" in text_lower or "hybride" in text_lower:
            return "hybrid"
        elif "on-site" in text_lower or "sur site" in text_lower or "onsite" in text_lower:
            return "on_site"
        return "unknown"