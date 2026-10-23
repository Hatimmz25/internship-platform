import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from dateutil import parser as date_parser
from sqlalchemy.orm import Session
from app.models.offer import InternshipOffer
from app.models.scraping import ScrapingSource

CONTENT_FIELDS = ("title", "description", "company")
UPDATABLE = ("title", "company", "location_raw", "country", "workplace_type",
             "internship_type", "description", "required_skills", "languages")


def _fingerprint(raw: Dict[str, Any]) -> str:
    sig = f"{raw.get('company','')}|{raw.get('title','')}|{raw.get('country','')}".lower()
    return hashlib.sha256(re.sub(r"[^a-z0-9|]", "", sig).encode()).hexdigest()


def _parse_dt(value: Any) -> Optional[datetime]:
    if not value:
        return None
    dt = value if isinstance(value, datetime) else date_parser.parse(str(value))
    return dt.astimezone(timezone.utc).replace(tzinfo=None) if dt.tzinfo else dt


def process_and_upsert_offer(
    db: Session, source: ScrapingSource, raw_item: Dict[str, Any]
) -> Tuple[InternshipOffer, bool, bool]:
    now = datetime.utcnow()
    canonical_url = str(raw_item.get("canonical_url"))
    fingerprint = raw_item.get("fingerprint") or _fingerprint(raw_item)

    existing = (
        db.query(InternshipOffer)
        .filter((InternshipOffer.canonical_url == canonical_url)
                | (InternshipOffer.fingerprint == fingerprint))
        .first()
    )

    if existing:
        # Only compare fields the scraper actually supplied.
        content_changed = any(
            k in raw_item and getattr(existing, k) != raw_item[k] for k in CONTENT_FIELDS
        )
        for field in UPDATABLE:
            if raw_item.get(field) is not None:
                setattr(existing, field, raw_item[field])
        if raw_item.get("title"):
            existing.normalized_title = raw_item.get("normalized_title") or raw_item["title"].lower()
        existing.last_seen_at = now
        db.commit()
        db.refresh(existing)
        return existing, False, content_changed

    title = raw_item.get("title") or ""
    new_offer = InternshipOffer(
        source_id=source.id,
        source_item_id=raw_item.get("source_item_id"),
        canonical_url=canonical_url,
        fingerprint=fingerprint,
        title=title,
        normalized_title=raw_item.get("normalized_title") or title.lower(),
        company=raw_item.get("company"),
        location_raw=raw_item.get("location_raw", "Europe"),
        country=raw_item.get("country", "Europe"),
        workplace_type=raw_item.get("workplace_type", "unknown"),
        internship_type=raw_item.get("internship_type", "pfe"),
        description=raw_item.get("description", ""),
        required_skills=raw_item.get("required_skills", []),
        languages=raw_item.get("languages", []),
        published_at=_parse_dt(raw_item.get("published_at")),
        first_seen_at=now,
        last_seen_at=now,
    )
    db.add(new_offer)
    db.commit()
    db.refresh(new_offer)
    return new_offer, True, False