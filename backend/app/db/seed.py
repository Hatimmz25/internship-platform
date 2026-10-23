"""
Synthetic Development Seed Script.
Populates PostgreSQL with an initial admin account, a source, and one synthetic offer.

Run `alembic upgrade head` first: this script does NOT create tables.
"""
from datetime import datetime

import app.models  # noqa: F401  (registers all ORM models)
from app.core.db import SessionLocal
from app.core.security import get_password_hash
from app.models.offer import InternshipOffer
from app.models.scraping import ScrapingSource
from app.models.user import User, UserRole


def seed_database():
    db = SessionLocal()
    try:
        # 1. Admin user (development credentials: change them outside local dev)
        admin = db.query(User).filter(User.email == "admin@internshipradar.ai").first()
        if not admin:
            admin = User(
                email="admin@internshipradar.ai",
                hashed_password=get_password_hash("Admin123456!"),
                role=UserRole.ADMIN.value,
                is_active=True,
            )
            db.add(admin)
            db.commit()

        # 2. Default scraping source
        source = db.query(ScrapingSource).filter(
            ScrapingSource.slug == "abg_master_internships").first()
        if not source:
            source = ScrapingSource(
                name="ABG - Stages Master 2 / Ingénieur",
                slug="abg_master_internships",
                base_url="https://www.abg.asso.fr",
                feed_url=None,
                is_active=False,  # enable once you've confirmed ABG's terms allow it
                rate_limit_rps=0.5,
            )
            db.add(source)
            db.commit()

        # 3. Synthetic internship listing
        offer = (
            db.query(InternshipOffer)
            .filter(InternshipOffer.canonical_url == "https://synth.example.com/pfe-ml-1")
            .first()
        )
        if not offer:
            now = datetime.utcnow()
            offer = InternshipOffer(
                source_id=source.id,
                source_item_id="SYNTH-001",
                canonical_url="https://synth.example.com/pfe-ml-1",
                fingerprint="synth_pfe_ml_fingerprint_001",
                title="Synthetic PFE - Applied AI / Computer Vision Research Intern",
                normalized_title="synthetic pfe - applied ai / computer vision research intern",
                company="Synthetic AI Research Labs",
                location_raw="Paris, France",
                country="France",
                workplace_type="hybrid",
                internship_type="pfe",
                description="Synthetic end-of-studies internship position focusing on PyTorch, Object Detection, and LLMs.",
                required_skills=["python", "pytorch", "opencv", "docker"],
                languages=["English", "French"],
                published_at=now,
                first_seen_at=now,
                last_seen_at=now,
            )
            db.add(offer)
            db.commit()

        print("Synthetic seed completed successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()