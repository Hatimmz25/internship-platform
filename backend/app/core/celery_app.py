from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "internship_radar_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.scraping_tasks", "app.tasks.matcher", "app.tasks.notifications"],
)
celery_app.conf.update(
    task_serializer="json", accept_content=["json"], result_serializer="json",
    timezone="UTC", enable_utc=True, task_track_started=True,
    task_time_limit=3600, task_soft_time_limit=3300,
)
celery_app.conf.beat_schedule = {
    "dispatch-enabled-scrapers-every-6-hours": {
        "task": "app.tasks.scraping_tasks.dispatch_scraping_tasks",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    "process-daily-email-digests": {
        "task": "app.tasks.notifications.process_daily_digests",
        "schedule": crontab(minute=0, hour=8),
    },
}