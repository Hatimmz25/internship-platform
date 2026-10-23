import logging
from datetime import datetime
from celery import shared_task
from app.core.db import SessionLocal
from app.models.match import OfferMatch
from app.models.notification import NotificationLog
from app.models.preference import AlertFrequency, Preference
from app.models.user import User
from app.services.email.factory import get_email_provider
from app.services.email.templates import generate_match_email

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="app.tasks.notifications.queue_match_notification_task",
             max_retries=3, default_retry_delay=60)
def queue_match_notification_task(self, match_id: int):
    db = SessionLocal()
    try:
        match = db.get(OfferMatch, match_id)
        if not match or not match.user.is_active:
            return "Ignored: Match missing or user inactive."
        pref = match.user.preference
        if not pref or pref.alert_frequency != AlertFrequency.INSTANT.value:
            return "Ignored: User does not want instant alerts."

        log = db.query(NotificationLog).filter_by(match_id=match.id).first()
        if log and log.status != "FAILED":
            return f"Ignored: Notification already exists with status {log.status}"
        if log:
            log.status = "QUEUED"
        else:
            log = NotificationLog(user_id=match.user_id, match_id=match.id, status="QUEUED")
            db.add(log)
        db.commit()

        provider = get_email_provider()
        email = generate_match_email(match.user, [match])
        try:
            provider.send_email(to_email=match.user.email, subject=email["subject"],
                                html_content=email["html_content"], text_content=email["text_content"])
        except Exception as exc:
            log.status = "FAILED"
            db.commit()
            raise self.retry(exc=exc)

        log.status = "SENT"
        log.sent_at = datetime.utcnow()
        db.commit()
        return "Instant notification sent successfully."
    finally:
        db.close()


@shared_task(name="app.tasks.notifications.process_daily_digests")
def process_daily_digests():
    db = SessionLocal()
    try:
        provider = get_email_provider()
        matches = (
            db.query(OfferMatch)
            .join(User, OfferMatch.user_id == User.id)
            .join(Preference, Preference.user_id == User.id)
            .filter(User.is_active.is_(True),
                    Preference.alert_frequency == AlertFrequency.DAILY.value,
                    ~OfferMatch.notifications.any())
            .all()
        )
        by_user = {}
        for m in matches:
            by_user.setdefault(m.user_id, []).append(m)

        dispatched = 0
        for user_id, user_matches in by_user.items():
            user = user_matches[0].user
            logs = [NotificationLog(user_id=user_id, match_id=m.id, status="QUEUED") for m in user_matches]
            db.add_all(logs)
            db.commit()
            email = generate_match_email(user, user_matches)
            try:
                provider.send_email(to_email=user.email, subject=email["subject"],
                                    html_content=email["html_content"], text_content=email["text_content"])
                status, sent_at = "SENT", datetime.utcnow()
                dispatched += 1
            except Exception as exc:
                logger.error("Digest delivery failed for %s: %s", user.email, exc)
                status, sent_at = "FAILED", None
            for log in logs:
                log.status, log.sent_at = status, sent_at
            db.commit()
        return f"Processed digests for {len(by_user)} users. Sent: {dispatched}"
    finally:
        db.close()