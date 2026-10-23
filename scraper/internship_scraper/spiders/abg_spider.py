import logging
import math
import re
from datetime import datetime
from typing import Optional

import scrapy

from internship_scraper.items import InternshipType, NormalizedInternshipOffer, WorkplaceType
from internship_scraper.spiders.base_spider import BaseInternshipSpider

logger = logging.getLogger(__name__)

PAGE_RE = re.compile(r"/recherche/page/(\d+)")


def _clean(text: Optional[str]) -> str:
    return re.sub(r"\s+", " ", (text or "").replace("\xa0", " ")).strip()


class AbgMasterInternshipsSpider(BaseInternshipSpider):
    """ABG (Association Bernard Gregory): 'Stage master 2 / Ingénieur' offers.

    The search page loads results by AJAX from /fr/candidatOffres/recherche/page/N,
    so we request that endpoint directly, as the site's own JavaScript does.
    """

    name = "abg_master_internships"  # must equal ScrapingSource.slug
    allowed_domains = ["abg.asso.fr"]
    start_urls = ["https://www.abg.asso.fr/fr/candidatOffres"]  # sets the session cookie

    SEARCH_URL = "https://www.abg.asso.fr/fr/candidatOffres/recherche/page/{page}"
    MAX_PAGES = 100
    WANTED_TYPE = "stage"  # matches 'Stage master 2 / Ingénieur'

    def parse(self, response):
        yield self._search_request(1)

    def _search_request(self, page: int) -> scrapy.Request:
        return scrapy.Request(
            self.SEARCH_URL.format(page=page),
            method="POST",
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "https://www.abg.asso.fr/fr/candidatOffres",
            },
            callback=self.parse_listing,
            cb_kwargs={"page": page},
            dont_filter=True,
        )

    def parse_listing(self, response, page: int = 1):
        for node in response.css("div.it_offre"):
            try:
                item = self._parse_offer(node, response)
            except Exception as exc:  # one bad listing must not stop the crawl
                self.stats_summary["errors"] += 1
                logger.warning("Skipping unparsable ABG listing: %s", exc)
                continue
            if item is not None:
                self.stats_summary["items_scraped"] += 1
                yield item

        if page == 1:
            pages = [int(n) for n in PAGE_RE.findall(response.text)]
            last = min(max(pages, default=1), self.MAX_PAGES)
            for next_page in range(2, last + 1):
                yield self._search_request(next_page)

    def _parse_offer(self, node, response) -> Optional[dict]:
        type_label = _clean(node.css("div.ligne_infos div.type::text").get()).lower()
        if self.WANTED_TYPE not in type_label:
            return None  # job or PhD thesis

        title = _clean(node.css("h2 a::text").get())
        href = node.css("h2 a::attr(href)").get()
        if not title or not href:
            return None

        company = _clean(" ".join(node.xpath(
            './/div[contains(@class,"societe")]//text()[not(ancestor::span)]').getall()))
        ref = _clean(node.css("div.ref::text").get()).replace("Ref.", "").strip()

        location = _clean(" ".join(node.css("div.adresse ::text").getall())).replace(" ,", ",")
        parts = [p.strip() for p in location.split(",") if p.strip()]
        country = parts[-1] if len(parts) > 1 else "France"

        snippet = _clean(" ".join(node.css("div.text ::text").getall())).rstrip(". ")
        keywords = _clean(" ".join(node.xpath(
            './/div[@class="mots"]//text()[not(ancestor::label)]').getall()))
        fields = ", ".join(
            _clean(t) for t in node.xpath(
                './/div[contains(@class,"expertises")]//text()'
                '[not(ancestor::label) and not(ancestor::span)]').getall()
            if _clean(t))

        description = snippet
        if keywords:
            description += f". Mots clés : {keywords}"
        if fields:
            description += f". Domaines : {fields}"

        published = None
        raw_date = _clean(node.css("div.l_date::text").get())
        if raw_date:
            try:
                published = datetime.strptime(raw_date, "%d/%m/%Y")
            except ValueError:
                pass

        offer = NormalizedInternshipOffer(
            source_name=self.name,
            source_item_id=ref or None,
            canonical_url=response.urljoin(href),
            title=title,
            normalized_title=title.lower(),
            company=company or "Non précisé",
            location_raw=location or "France",
            country=country,
            workplace_type=WorkplaceType.UNKNOWN,
            internship_type=InternshipType.PFE,  # 'Stage master 2 / Ingénieur'
            description=description or title,
            published_at=published,
        )
        return offer.model_dump()