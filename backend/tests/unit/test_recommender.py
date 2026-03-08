"""Unit tests for the doctor recommendation service."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tahalilai.database import Base
from tahalilai.models import Doctor
from tahalilai.services.recommender import (
    CANONICAL_SPECIALITIES,
    extract_recommended_specialities,
    find_recommended_doctors,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db_session():
    """In-memory SQLite session with the Doctor table created."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture()
def seeded_db(db_session):
    """DB session pre-populated with sample doctors."""
    doctors = [
        Doctor(name="Dr. Alami", primary_speciality="Cardiologue", city="Casablanca", phone="0600000001", address="Rue 1"),
        Doctor(name="Dr. Bennani", primary_speciality="Cardiologue", city="Rabat", phone="0600000002", address="Rue 2"),
        Doctor(name="Dr. Chraibi", primary_speciality="Dermatologue", city="Casablanca", phone="0600000003", address="Rue 3"),
        Doctor(name="Dr. Dahbi", primary_speciality="Endocrinologue", city="Casablanca", phone="0600000004", address="Rue 4"),
        Doctor(name="Dr. El Fassi", primary_speciality="Endocrinologue", city="Rabat", phone="0600000005", address="Rue 5"),
        Doctor(name="Dr. Filali", primary_speciality="Médecin généraliste", city="Casablanca", phone="0600000006", address="Rue 6"),
        Doctor(name="Dr. Ghali", primary_speciality="Médecin généraliste", city="Marrakech", phone="0600000007", address="Rue 7"),
        Doctor(name="Dr. Hamdi", primary_speciality="Neurologue", city="Casablanca", phone="0600000008", address="Rue 8"),
    ]
    db_session.add_all(doctors)
    db_session.commit()
    return db_session


# ---------------------------------------------------------------------------
# CANONICAL_SPECIALITIES
# ---------------------------------------------------------------------------


class TestCanonicalSpecialities:
    """Tests for the canonical speciality list."""

    def test_list_is_not_empty(self) -> None:
        assert len(CANONICAL_SPECIALITIES) > 0

    def test_contains_generaliste(self) -> None:
        assert "Médecin généraliste" in CANONICAL_SPECIALITIES

    def test_contains_cardiologue(self) -> None:
        assert "Cardiologue" in CANONICAL_SPECIALITIES

    def test_no_duplicates(self) -> None:
        assert len(CANONICAL_SPECIALITIES) == len(set(CANONICAL_SPECIALITIES))


# ---------------------------------------------------------------------------
# extract_recommended_specialities
# ---------------------------------------------------------------------------


class TestExtractRecommendedSpecialities:
    """Tests for Gemini-powered speciality extraction."""

    @patch("tahalilai.services.recommender._GEMINI_AVAILABLE", False)
    def test_returns_default_when_gemini_unavailable(self) -> None:
        """Without Gemini, should return default generaliste + routine."""
        result = extract_recommended_specialities("Some analysis text")
        assert result["specialities"] == ["Médecin généraliste"]
        assert result["urgency"] == "routine"

    @patch("tahalilai.services.recommender._GEMINI_AVAILABLE", True)
    @patch("tahalilai.services.recommender.get_settings")
    def test_returns_default_when_no_api_key(self, mock_settings: MagicMock) -> None:
        """Without API key, should return default."""
        mock_settings.return_value.gemini_api_key = ""
        result = extract_recommended_specialities("Some analysis text")
        assert result["specialities"] == ["Médecin généraliste"]
        assert result["urgency"] == "routine"

    @patch("tahalilai.services.recommender._GEMINI_AVAILABLE", True)
    @patch("tahalilai.services.recommender.genai")
    @patch("tahalilai.services.recommender.get_settings")
    def test_parses_gemini_response(self, mock_settings: MagicMock, mock_genai: MagicMock) -> None:
        """Should parse a valid Gemini JSON response."""
        mock_settings.return_value.gemini_api_key = "test-key"
        mock_settings.return_value.gemini_model = "gemini-test"

        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "specialities": ["Médecin généraliste", "Cardiologue"],
            "urgency": "soon",
        })
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response

        result = extract_recommended_specialities("High cholesterol detected in blood work")
        assert "Cardiologue" in result["specialities"]
        assert result["urgency"] == "soon"

    @patch("tahalilai.services.recommender._GEMINI_AVAILABLE", True)
    @patch("tahalilai.services.recommender.genai")
    @patch("tahalilai.services.recommender.get_settings")
    def test_handles_markdown_fenced_response(self, mock_settings: MagicMock, mock_genai: MagicMock) -> None:
        """Should strip markdown code fences from Gemini response."""
        mock_settings.return_value.gemini_api_key = "test-key"
        mock_settings.return_value.gemini_model = "gemini-test"

        mock_response = MagicMock()
        mock_response.text = '```json\n{"specialities": ["Endocrinologue"], "urgency": "urgent"}\n```'
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response

        result = extract_recommended_specialities("Critically high blood sugar")
        assert "Endocrinologue" in result["specialities"]
        assert result["urgency"] == "urgent"

    @patch("tahalilai.services.recommender._GEMINI_AVAILABLE", True)
    @patch("tahalilai.services.recommender.genai")
    @patch("tahalilai.services.recommender.get_settings")
    def test_returns_default_on_gemini_exception(self, mock_settings: MagicMock, mock_genai: MagicMock) -> None:
        """On API error, should gracefully return default."""
        mock_settings.return_value.gemini_api_key = "test-key"
        mock_settings.return_value.gemini_model = "gemini-test"
        mock_genai.Client.return_value.models.generate_content.side_effect = RuntimeError("API error")

        result = extract_recommended_specialities("Analysis text")
        assert result["specialities"] == ["Médecin généraliste"]
        assert result["urgency"] == "routine"

    @patch("tahalilai.services.recommender._GEMINI_AVAILABLE", True)
    @patch("tahalilai.services.recommender.genai")
    @patch("tahalilai.services.recommender.get_settings")
    def test_returns_default_on_invalid_json(self, mock_settings: MagicMock, mock_genai: MagicMock) -> None:
        """On malformed JSON, should return default."""
        mock_settings.return_value.gemini_api_key = "test-key"
        mock_settings.return_value.gemini_model = "gemini-test"

        mock_response = MagicMock()
        mock_response.text = "Not valid JSON at all"
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response

        result = extract_recommended_specialities("Analysis text")
        assert result["specialities"] == ["Médecin généraliste"]

    @patch("tahalilai.services.recommender._GEMINI_AVAILABLE", True)
    @patch("tahalilai.services.recommender.genai")
    @patch("tahalilai.services.recommender.get_settings")
    def test_truncates_long_analysis(self, mock_settings: MagicMock, mock_genai: MagicMock) -> None:
        """Analysis text > 3000 chars should be truncated in the prompt."""
        mock_settings.return_value.gemini_api_key = "test-key"
        mock_settings.return_value.gemini_model = "gemini-test"

        mock_response = MagicMock()
        mock_response.text = json.dumps({"specialities": ["Médecin généraliste"], "urgency": "routine"})
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response

        long_text = "x" * 5000
        extract_recommended_specialities(long_text)

        call_args = mock_genai.Client.return_value.models.generate_content.call_args
        prompt = call_args.kwargs.get("contents") or call_args[1].get("contents") or call_args[0][0]
        # The analysis part should be truncated to 3000 chars
        assert "x" * 3000 in str(prompt)
        assert "x" * 5000 not in str(prompt)


# ---------------------------------------------------------------------------
# find_recommended_doctors
# ---------------------------------------------------------------------------


class TestFindRecommendedDoctors:
    """Tests for database doctor lookups."""

    def test_finds_by_speciality(self, seeded_db) -> None:
        """Should return doctors matching the given speciality."""
        results = find_recommended_doctors(["Cardiologue"], city=None, db=seeded_db)
        assert len(results) == 2
        assert all(r["speciality"] == "Cardiologue" for r in results)

    def test_prioritizes_city(self, seeded_db) -> None:
        """When city is given, doctors from that city should come first."""
        results = find_recommended_doctors(["Cardiologue"], city="Casablanca", db=seeded_db)
        assert len(results) >= 1
        assert results[0]["city"] == "Casablanca"

    def test_fills_from_other_cities(self, seeded_db) -> None:
        """If city has fewer doctors than limit, fill from other cities."""
        results = find_recommended_doctors(
            ["Endocrinologue"], city="Casablanca", db=seeded_db, limit_per_speciality=5
        )
        cities = {r["city"] for r in results}
        assert "Rabat" in cities  # Should fill from Rabat

    def test_multiple_specialities(self, seeded_db) -> None:
        """Should return doctors for each requested speciality."""
        results = find_recommended_doctors(
            ["Cardiologue", "Dermatologue"], city=None, db=seeded_db
        )
        specs = {r["speciality"] for r in results}
        assert "Cardiologue" in specs
        assert "Dermatologue" in specs

    def test_no_duplicates(self, seeded_db) -> None:
        """Same doctor should not appear twice even if matching multiple queries."""
        results = find_recommended_doctors(
            ["Médecin généraliste", "Médecin généraliste"], city=None, db=seeded_db
        )
        ids = [r["id"] for r in results]
        assert len(ids) == len(set(ids))

    def test_empty_specialities_returns_empty(self, seeded_db) -> None:
        """Empty speciality list should return no results."""
        results = find_recommended_doctors([], city=None, db=seeded_db)
        assert results == []

    def test_unknown_speciality_returns_empty(self, seeded_db) -> None:
        """Non-existent speciality should return empty list."""
        results = find_recommended_doctors(["Chirurgien spatial"], city=None, db=seeded_db)
        assert results == []

    def test_respects_limit(self, seeded_db) -> None:
        """Should not return more than limit_per_speciality per speciality."""
        results = find_recommended_doctors(
            ["Cardiologue"], city=None, db=seeded_db, limit_per_speciality=1
        )
        assert len(results) == 1

    def test_result_format(self, seeded_db) -> None:
        """Each result dict should have the expected keys."""
        results = find_recommended_doctors(["Cardiologue"], city=None, db=seeded_db)
        assert len(results) > 0
        doc = results[0]
        expected_keys = {"id", "title", "name", "speciality", "phone", "address", "city", "image_url", "profile_url"}
        assert expected_keys.issubset(doc.keys())
