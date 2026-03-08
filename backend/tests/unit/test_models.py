"""Unit tests for SQLAlchemy ORM models."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from tahalilai.database import Base
from tahalilai.models import Doctor


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db_session():
    """In-memory SQLite session with all tables created."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture()
def engine():
    """In-memory SQLite engine for schema inspection."""
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


# ---------------------------------------------------------------------------
# Doctor model schema
# ---------------------------------------------------------------------------


class TestDoctorSchema:
    """Tests for the Doctor table structure."""

    def test_table_name(self) -> None:
        assert Doctor.__tablename__ == "doctors"

    def test_table_created(self, engine) -> None:
        """The doctors table should exist after create_all."""
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        assert "doctors" in tables

    def test_columns_exist(self, engine) -> None:
        """All expected columns should be present."""
        inspector = inspect(engine)
        columns = {c["name"] for c in inspector.get_columns("doctors")}
        expected = {
            "id", "title", "name", "primary_speciality", "specialities",
            "phone", "address", "city", "description", "languages",
            "image_url", "profile_url", "source_site",
            "latitude", "longitude", "google_rating", "google_review_count",
        }
        assert expected.issubset(columns)

    def test_indexes_exist(self, engine) -> None:
        """Key indexes should be created."""
        inspector = inspect(engine)
        indexes = inspector.get_indexes("doctors")
        index_names = {idx["name"] for idx in indexes}
        # Composite index
        assert "ix_doctors_city_speciality" in index_names


# ---------------------------------------------------------------------------
# Doctor model CRUD
# ---------------------------------------------------------------------------


class TestDoctorCRUD:
    """Tests for Doctor create, read, update, delete."""

    def test_create_doctor(self, db_session) -> None:
        """Should insert a doctor record successfully."""
        doc = Doctor(name="Dr. Test", primary_speciality="Cardiologue", city="Casablanca")
        db_session.add(doc)
        db_session.commit()
        assert doc.id is not None
        assert doc.id > 0

    def test_read_doctor(self, db_session) -> None:
        """Should retrieve a doctor by id."""
        doc = Doctor(name="Dr. Alami", primary_speciality="Dermatologue", city="Rabat")
        db_session.add(doc)
        db_session.commit()

        fetched = db_session.query(Doctor).filter_by(id=doc.id).first()
        assert fetched is not None
        assert fetched.name == "Dr. Alami"
        assert fetched.city == "Rabat"

    def test_update_doctor(self, db_session) -> None:
        """Should update a doctor's fields."""
        doc = Doctor(name="Dr. Old", primary_speciality="Généraliste", city="Fes")
        db_session.add(doc)
        db_session.commit()

        doc.name = "Dr. New"
        doc.phone = "0600000000"
        db_session.commit()

        fetched = db_session.query(Doctor).filter_by(id=doc.id).first()
        assert fetched.name == "Dr. New"
        assert fetched.phone == "0600000000"

    def test_delete_doctor(self, db_session) -> None:
        """Should delete a doctor record."""
        doc = Doctor(name="Dr. Delete", primary_speciality="Pédiatre", city="Tanger")
        db_session.add(doc)
        db_session.commit()
        doc_id = doc.id

        db_session.delete(doc)
        db_session.commit()

        assert db_session.query(Doctor).filter_by(id=doc_id).first() is None

    def test_default_values(self, db_session) -> None:
        """Fields with defaults should be empty strings or None."""
        doc = Doctor(name="Dr. Minimal", primary_speciality="Test", city="Test")
        db_session.add(doc)
        db_session.commit()

        assert doc.title == ""
        assert doc.phone == ""
        assert doc.address == ""
        assert doc.latitude is None
        assert doc.longitude is None
        assert doc.google_rating is None
        assert doc.google_review_count is None

    def test_nullable_fields(self, db_session) -> None:
        """Latitude, longitude, ratings should accept None."""
        doc = Doctor(
            name="Dr. Nullable",
            primary_speciality="Test",
            city="Test",
            latitude=None,
            longitude=None,
            google_rating=None,
            google_review_count=None,
        )
        db_session.add(doc)
        db_session.commit()
        assert doc.latitude is None

    def test_geocoding_fields(self, db_session) -> None:
        """Should store and retrieve lat/lng correctly."""
        doc = Doctor(
            name="Dr. Geo",
            primary_speciality="Test",
            city="Casablanca",
            latitude=33.5731,
            longitude=-7.5898,
        )
        db_session.add(doc)
        db_session.commit()

        fetched = db_session.query(Doctor).filter_by(id=doc.id).first()
        assert abs(fetched.latitude - 33.5731) < 0.001
        assert abs(fetched.longitude - (-7.5898)) < 0.001

    def test_rating_fields(self, db_session) -> None:
        """Should store and retrieve Google rating data."""
        doc = Doctor(
            name="Dr. Rated",
            primary_speciality="Test",
            city="Marrakech",
            google_rating=4.5,
            google_review_count=120,
        )
        db_session.add(doc)
        db_session.commit()

        fetched = db_session.query(Doctor).filter_by(id=doc.id).first()
        assert fetched.google_rating == 4.5
        assert fetched.google_review_count == 120


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------


class TestDoctorQueries:
    """Tests for common query patterns used by the API."""

    @pytest.fixture(autouse=True)
    def _seed(self, db_session) -> None:
        self.db = db_session
        doctors = [
            Doctor(name="Dr. A", primary_speciality="Cardiologue", city="Casablanca"),
            Doctor(name="Dr. B", primary_speciality="Cardiologue", city="Rabat"),
            Doctor(name="Dr. C", primary_speciality="Dermatologue", city="Casablanca"),
            Doctor(name="Dr. D", primary_speciality="Neurologue", city="Fes"),
        ]
        db_session.add_all(doctors)
        db_session.commit()

    def test_filter_by_city(self) -> None:
        results = self.db.query(Doctor).filter(Doctor.city.ilike("casablanca")).all()
        assert len(results) == 2

    def test_filter_by_speciality(self) -> None:
        results = self.db.query(Doctor).filter(Doctor.primary_speciality.ilike("cardiologue")).all()
        assert len(results) == 2

    def test_filter_by_city_and_speciality(self) -> None:
        results = (
            self.db.query(Doctor)
            .filter(Doctor.city.ilike("casablanca"), Doctor.primary_speciality.ilike("cardiologue"))
            .all()
        )
        assert len(results) == 1
        assert results[0].name == "Dr. A"

    def test_search_by_name(self) -> None:
        results = self.db.query(Doctor).filter(Doctor.name.ilike("%Dr. C%")).all()
        assert len(results) == 1
        assert results[0].primary_speciality == "Dermatologue"

    def test_count_by_city(self) -> None:
        from sqlalchemy import func
        results = (
            self.db.query(Doctor.city, func.count(Doctor.id))
            .group_by(Doctor.city)
            .all()
        )
        city_counts = dict(results)
        assert city_counts["Casablanca"] == 2
        assert city_counts["Rabat"] == 1
        assert city_counts["Fes"] == 1
