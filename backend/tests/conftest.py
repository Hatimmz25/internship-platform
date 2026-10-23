import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

_base = make_url(os.environ.get(
    "DATABASE_URL", "postgresql+psycopg2://postgres:postgres@postgres:5432/internship_radar"))
_test_db = _base.database if _base.database.endswith("_test") else _base.database + "_test"
os.environ["DATABASE_URL"] = _base.set(database=_test_db).render_as_string(hide_password=False)
assert _test_db.endswith("_test")

_admin = create_engine(_base.set(database="postgres"), isolation_level="AUTOCOMMIT")
with _admin.connect() as c:
    if not c.execute(text("SELECT 1 FROM pg_database WHERE datname=:n"), {"n": _test_db}).scalar():
        c.execute(text(f'CREATE DATABASE "{_test_db}"'))

from app.core.db import Base, SessionLocal, engine  # noqa: E402
from app.core.celery_app import celery_app          # noqa: E402
import app.models                                   # noqa: E402,F401

celery_app.conf.task_always_eager = True
celery_app.conf.task_eager_propagates = True


@pytest.fixture(scope="session", autouse=True)
def _schema():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture(autouse=True)
def _clean_tables():
    names = ",".join(t.name for t in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {names} RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
def db_session():
    s = SessionLocal()
    yield s
    s.close()