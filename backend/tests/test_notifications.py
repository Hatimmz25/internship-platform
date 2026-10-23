from unittest.mock import MagicMock, patch

from app.core.db import SessionLocal
from app.models import (
    AlertFrequency,
    InternshipOffer,
    NotificationLog,
    OfferMatch,
    Preference,
    ScrapingSource,
    User,
    UserRole,
)
from app.services.email.templates import generate_match_email
from app.tasks.notifications import process_daily_digests, queue_match_notification_task


def _setup(db, email: str, frequency: str):
    source = ScrapingSource(name="t", slug="t", base_url="https://t.example")
    db.add(source)
    db.commit()

    user = User(email=email, hashed_password="pw", role=UserRole.USER.value)
    db.add(user)
    db.commit()

    db.add(Preference(user_id=user.id, alert_frequency=frequency))
    offer = InternshipOffer(
        source_id=source.id,
        canonical_url="http://i1",
        fingerprint="f1",
        title="Offer",
        company="Co",
    )
    db.add(offer)
    db.commit()

    match = OfferMatch(user_id=user.id, offer_id=offer.id, score=90.0)
    db.add(match)
    db.commit()
    return match.id


def test_generate_match_email_rendering():
    user = User(id=1, email="test@example.com")
    offer = InternshipOffer(
        title="AI Engineer", company="Tech", country="France",
        workplace_type="remote", internship_type="pfe", canonical_url="http://test.com",
    )
    match = OfferMatch(user=user, offer=offer, score=95.0, reasons=["Role match"])

    payload = generate_match_email(user, [match])

    assert "AI Engineer" in payload["subject"]
    assert "Tech" in payload["html_content"]
    assert "95.0%" in payload["text_content"]
    assert "token=" in payload["html_content"]  # secure unsubscribe link present


def test_email_escapes_scraped_html():
    user = User(id=1, email="test@example.com")
    offer = InternshipOffer(title="<script>x</script>", company="Co", canonical_url="http://t.com")
    match = OfferMatch(user=user, offer=offer, score=50.0, reasons=[])

    payload = generate_match_email(user, [match])

    assert "<script>" not in payload["html_content"]


@patch("app.tasks.notifications.get_email_provider")
def test_idempotent_instant_notification(mock_get_provider):
    provider = MagicMock()
    mock_get_provider.return_value = provider
    db = SessionLocal()
    try:
        match_id = _setup(db, "instant@example.com", AlertFrequency.INSTANT.value)

        # Call 1: sends
        queue_match_notification_task(match_id)
        logs = db.query(NotificationLog).filter_by(match_id=match_id).all()
        assert len(logs) == 1
        assert logs[0].status == "SENT"
        assert provider.send_email.call_count == 1

        # Call 2: suppressed by the idempotency check
        queue_match_notification_task(match_id)
        assert db.query(NotificationLog).filter_by(match_id=match_id).count() == 1
        assert provider.send_email.call_count == 1
    finally:
        db.close()


@patch("app.tasks.notifications.get_email_provider")
def test_daily_digest_sends_once(mock_get_provider):
    provider = MagicMock()
    mock_get_provider.return_value = provider
    db = SessionLocal()
    try:
        match_id = _setup(db, "daily@example.com", AlertFrequency.DAILY.value)

        process_daily_digests()
        logs = db.query(NotificationLog).filter_by(match_id=match_id).all()
        assert len(logs) == 1
        assert logs[0].status == "SENT"
        assert provider.send_email.call_count == 1

        process_daily_digests()  # nothing new to send
        assert provider.send_email.call_count == 1
    finally:
        db.close()