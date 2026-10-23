"""
Tests for the Internship Relevance and Ranking Engine.
Covers exact/partial skills, locations, PFE constraints, exclusions, missing data,
duplicate prevention and rematching.
"""
from types import SimpleNamespace

from app.core.db import SessionLocal
from app.models import InternshipOffer, OfferMatch, Preference, ScrapingSource, User, UserRole
from app.services.matcher import calculate_match_score
from app.tasks.matcher import match_new_offer_task, rematch_subscriber_preferences_task


def test_exact_skill_matches():
    offer = SimpleNamespace(
        title="Python Backend Intern",
        normalized_title="python backend intern",
        company="Tech Corp",
        description="Looking for Python and FastApi developer",
        required_skills=["python", "fastapi"],
        country="France",
        workplace_type="remote",
        internship_type="standard",
        languages=["english"],
        location_raw="Paris, France",
    )
    pref = SimpleNamespace(
        target_roles=["backend"],
        skills=["python", "fastapi"],
        preferred_countries=["france"],
        workplace_types=["remote"],
        internship_types=[],
        preferred_languages=["english"],
        keywords=[],
        exclusion_keywords=[],
    )
    res = calculate_match_score(offer, pref)
    assert res["is_excluded"] is False
    assert res["score"] >= 80.0
    assert res["breakdown"]["skills"] == 25.0


def test_partial_skill_matches():
    offer = SimpleNamespace(
        title="Software Intern",
        required_skills=["python"],
        country="France",
    )
    pref = SimpleNamespace(
        skills=["python", "docker", "kubernetes", "react"],
        preferred_countries=["france"],
    )
    res = calculate_match_score(offer, pref)
    assert res["is_excluded"] is False
    # 1 of 4 skills matched = 25% of 25 pts = 6.25 pts
    assert res["breakdown"]["skills"] == 6.25


def test_location_and_remote_preferences():
    offer = SimpleNamespace(
        title="Data Engineer",
        country="Germany",
        workplace_type="onsite",
        location_raw="Berlin, Germany",
    )
    pref = SimpleNamespace(
        preferred_countries=["france"],
        workplace_types=["remote"],
    )
    res = calculate_match_score(offer, pref)
    assert res["breakdown"]["location"] == 0.0


def test_pfe_only_preferences():
    offer = SimpleNamespace(title="Summer Intern", internship_type="summer")
    pref = SimpleNamespace(internship_types=["pfe"])
    res = calculate_match_score(offer, pref)
    assert res["is_excluded"] is True
    assert "Required PFE" in res["exclusion_reason"]


def test_excluded_keywords():
    offer = SimpleNamespace(
        title="Senior Lead Developer Intern",
        description="Must have 10 years experience",
    )
    pref = SimpleNamespace(exclusion_keywords=["senior", "lead"])
    res = calculate_match_score(offer, pref)
    assert res["is_excluded"] is True
    assert "negative keyword" in res["exclusion_reason"]


def test_missing_data_safety():
    res = calculate_match_score(SimpleNamespace(), SimpleNamespace())
    assert res["is_excluded"] is False
    assert 0.0 <= res["score"] <= 100.0


def test_duplicate_prevention_and_preference_update_db():
    # The conftest fixtures give every test an empty, isolated *_test database.
    db = SessionLocal()
    try:
        source = ScrapingSource(name="t", slug="t", base_url="https://t.example")
        db.add(source)
        db.commit()

        offer = InternshipOffer(
            source_id=source.id,
            canonical_url="https://t.example/1",
            fingerprint="fp1",
            title="Synthetic AI Intern",
            normalized_title="synthetic ai intern",
            company="Co",
            description="Synthetic python project",
            required_skills=["python"],
            internship_type="pfe",
        )
        user = User(email="matcher_test@example.com", hashed_password="pw", role=UserRole.SUBSCRIBER.value)
        db.add_all([offer, user])
        db.commit()

        pref = Preference(
            user_id=user.id,
            target_roles=["ai"],
            skills=["python"],
            min_relevance_score=40.0,
        )
        db.add(pref)
        db.commit()
        offer_id, user_id = offer.id, user.id

        # First run creates one match
        match_new_offer_task(offer_id)
        matches = db.query(OfferMatch).filter_by(user_id=user_id, offer_id=offer_id).all()
        assert len(matches) == 1

        # Second run must not create a duplicate
        match_new_offer_task(offer_id)
        assert db.query(OfferMatch).filter_by(user_id=user_id, offer_id=offer_id).count() == 1

        # Preference change + rematch: offer contains "synthetic", so the match disappears
        pref.exclusion_keywords = ["synthetic"]
        db.commit()
        rematch_subscriber_preferences_task(user_id)
        assert db.query(OfferMatch).filter_by(user_id=user_id, offer_id=offer_id).count() == 0
    finally:
        db.close()