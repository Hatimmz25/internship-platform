import scrapy
import xml.etree.ElementTree as ET
from dateutil import parser as date_parser
from internship_scraper.spiders.base_spider import BaseInternshipSpider
from internship_scraper.items import NormalizedInternshipOffer, WorkplaceType, InternshipType


class EuropaJobsRSSSpider(BaseInternshipSpider):
    name = "europa_jobs_rss"
    allowed_domains = ["europa.eu", "ec.europa.eu"]
    # Verified active feed URL
    start_urls = ["https://ec.europa.eu/commission/presscorner/api/rss?language=en"]

    def parse(self, response):
        """Parse compliant XML/RSS feed entries."""
        try:
            root = ET.fromstring(response.body)
        except ET.ParseError:
            self.logger.error("Failed to parse XML payload from feed.")
            return

        channel = root.find("channel")
        if channel is None:
            return

        for item in channel.findall("item"):
            title = item.findtext("title", default="").strip()
            link = item.findtext("link", default="").strip()
            description_raw = item.findtext("description", default="").strip()
            pub_date_str = item.findtext("pubDate", default="")

            pub_date = None
            if pub_date_str:
                try:
                    pub_date = date_parser.parse(pub_date_str)
                except Exception:
                    pub_date = None

            cleaned_desc = self.clean_html(description_raw)

            offer = NormalizedInternshipOffer(
                source_name=self.name,
                source_item_id=item.findtext("guid", default=link),
                canonical_url=link,
                title=title,
                normalized_title=title.lower(),
                company="European Commission",
                location_raw="Brussels, Europe",
                country="Europe",
                workplace_type=WorkplaceType(self.parse_workplace_type(cleaned_desc)),
                internship_type=InternshipType.PFE if "pfe" in cleaned_desc.lower() or "master" in cleaned_desc.lower() else InternshipType.GENERAL,
                description=cleaned_desc or title,
                published_at=pub_date
            )

            self.stats_summary["items_scraped"] += 1
            yield offer.model_dump()