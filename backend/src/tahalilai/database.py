"""SQLite database setup using SQLAlchemy.

Provides:
- Engine and session factory
- Base declarative class
- ``get_db()`` FastAPI dependency for per-request sessions
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
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
    connect_args={"check_same_thread": False},  # required for SQLite + FastAPI
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency that provides a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
