import json
import logging
import os
import subprocess
from datetime import datetime

from celery import shared_task

from app.core.db import SessionLocal
from app.core.locks import redis_lock
from app.models.scraping import RunStatus, ScrapingRun, ScrapingSource
from app.services.ingestion import process_and_upsert_offer
from app.tasks.matcher import match_new_offer_task

logger = logging.getLogger(__name__)


@shared_task(name="app.tasks.scraping_tasks.dispatch_scraping_tasks")
def dispatch_scraping_tasks():
    """Dispatches individual asynchronous scraping tasks for all active sources."""
    db = SessionLocal()
    try:
        active_sources = db.query(ScrapingSource).filter(ScrapingSource.is_active == True).all()  # noqa: E712
        for source in active_sources:
            scrape_source_task.delay(source.id)
        return {"dispatched_sources": len(active_sources)}
    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.tasks.scraping_tasks.scrape_source_task",
    max_retries=3,
    default_retry_delay=300,  # 5 minute backoff on failure
)
def scrape_source_task(self, source_id: int):
    """Executes a Scrapy spider as a subprocess and processes the scraped JSON output."""
    lock_name = f"scrape_lock_source_{source_id}"

    with redis_lock(lock_name, timeout=1800) as acquired:
        if not acquired:
            logger.warning(f"Source {source_id} is already being scraped. Skipping duplicate execution.")
            return {"status": "skipped_locked", "source_id": source_id}

        db = SessionLocal()
        run_record = None
        metrics = {"collected": 0, "new": 0, "updated": 0, "unchanged": 0, "skipped": 0}

        try:
            source = db.get(ScrapingSource, source_id)
            if not source:
                return {"status": "error", "error": "Source not found"}

            run_record = ScrapingRun(
                source_id=source.id,
                status=RunStatus.PENDING.value,
                started_at=datetime.utcnow(),
            )
            db.add(run_record)
            db.commit()

            # The spider name must equal source.slug.
            output_file = f"/tmp/offers_{run_record.id}.json"
            scraper_dir = "/app/scraper"
            command = ["scrapy", "crawl", source.slug, "-O", output_file]
            if source.rate_limit_rps and source.rate_limit_rps > 0:
                command += ["-s", f"DOWNLOAD_DELAY={1.0 / source.rate_limit_rps:.2f}"]

            result = subprocess.run(
                command, cwd=scraper_dir, capture_output=True, text=True, timeout=3000
            )
            if result.returncode != 0:
                raise Exception(f"Scrapy failed: {result.stderr[-2000:]}")

               if os.path.exists(output_file):
       raw_items = []
    if os.path.getsize(output_file) > 0:
           with open(output_file, "r") as f:
               raw_items = json.load(f)

       for raw_item in raw_items:
           metrics["collected"] += 1
           try:
               offer, is_new, is_updated = process_and_upsert_offer(db, source, raw_item)
           except Exception as item_exc:
               db.rollback()
               metrics["skipped"] += 1
               logger.warning("Skipping bad item %s: %s", raw_item.get("canonical_url"), item_exc)
               continue

           if is_new:
               metrics["new"] += 1
               match_new_offer_task.delay(offer.id)
           elif is_updated:
               metrics["updated"] += 1
           else:
               metrics["unchanged"] += 1

       os.remove(output_file)

            run_record.status = RunStatus.SUCCESS.value
            run_record.items_found = metrics["collected"]
            run_record.items_new = metrics["new"]
            run_record.items_updated = metrics["updated"]
            run_record.finished_at = datetime.utcnow()
            db.commit()

            return {"status": "success", "source_id": source_id, "metrics": metrics}

        except Exception as exc:
            db.rollback()
            if run_record is not None:
                run_record.status = RunStatus.FAILED.value
                run_record.error_log = str(exc)
                run_record.finished_at = datetime.utcnow()
                db.commit()
            logger.error(f"Scraping failed for source {source_id}: {exc}")
            raise self.retry(exc=exc)
        finally:
            db.close()