import os

from scrapy.http import HtmlResponse, Request

from internship_scraper.spiders.abg_spider import AbgMasterInternshipsSpider

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "abg_list.html")
URL = "https://www.abg.asso.fr/fr/candidatOffres/recherche/page/1"


def _response():
    with open(FIXTURE, "rb") as f:
        body = f.read()
    return HtmlResponse(url=URL, body=body, encoding="utf-8", request=Request(URL))


def test_abg_listing_keeps_only_master_internships_and_paginates():
    spider = AbgMasterInternshipsSpider()
    out = list(spider.parse_listing(_response(), page=1))
    items = [o for o in out if isinstance(o, dict)]
    requests = [o for o in out if not isinstance(o, dict)]

    assert items, "expected at least one 'Stage master 2' offer in the fixture"
    for it in items:
        assert it["source_name"] == "abg_master_internships"
        assert it["internship_type"] == "pfe"
        assert it["source_item_id"].startswith("ABG-")
        assert it["canonical_url"].startswith(
            "https://www.abg.asso.fr/fr/candidatOffres/show/id_offre/")

    assert requests, "expected pagination requests"
    assert all(r.method == "POST" for r in requests)