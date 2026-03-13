"""SQLite database setup using SQLAlchemy.

Provides:
- Engine and session factory
- Base declarative class
- ``get_db()`` FastAPI dependency for per-request sessions
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from tahalilai.config import get_settings


class Base(DeclarativeBase):
    pass


def _get_db_url() -> str:
    # DB lives in data/ (NOT uploads/) so it's never served by StaticFiles.
    db_path = get_settings().data_dir / "tahalilai.db"
    return f"sqlite:///{db_path}"


engine = create_engine(
    _get_db_url(),
    connect_args={"check_same_thread": False, "timeout": 30},
    echo=False,
)

# Enable WAL mode so reads (API requests) aren't blocked by the seeder's bulk writes
@event.listens_for(engine, "connect")
def _set_wal_mode(dbapi_conn, _):
    dbapi_conn.execute("PRAGMA journal_mode=WAL")
    dbapi_conn.execute("PRAGMA busy_timeout=30000")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency that provides a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
