"""Tests für den Quiz-Service."""


import json
import tempfile
from pathlib import Path

import pytest

from losungs_bot.quiz_service import QuizQuestion, QuizService, QuizStateManager


class TestQuizQuestion:
    """Tests für das QuizQuestion-Dataclass."""

    def test_create_quiz_question(self):
        quiz = QuizQuestion(
            question="Aus welchem Buch stammt dieser Vers?",
            options=["Genesis", "Exodus", "Jesaja", "Psalmen"],
            correct_index=2,
            explanation="Jesaja war ein Prophet.",
            losung_reference="Jesaja 41,10",
        )
        assert quiz.question == "Aus welchem Buch stammt dieser Vers?"
        assert len(quiz.options) == 4
        assert quiz.correct_index == 2
        assert quiz.options[quiz.correct_index] == "Jesaja"


class TestQuizFormatting:
    """Tests für die Post-Formatierung."""

    @pytest.fixture
    def quiz(self):
        return QuizQuestion(
            question="Aus welchem Buch stammt dieser Vers?",
            options=["Genesis", "Exodus", "Jesaja", "Psalmen"],
            correct_index=2,
            explanation="Jesaja war ein Prophet im 8. Jahrhundert v. Chr.",
            losung_reference="Jesaja 41,10",
        )

    @pytest.fixture
    def service(self):
        # Service ohne echten API-Key erstellen (nur für Formatierung)
        service = object.__new__(QuizService)
        return service

    def test_format_quiz_post(self, service, quiz):
        text = service.format_quiz_post(quiz, "Fürchte dich nicht, ich bin mit dir.")
        assert "Bibelquiz" in text
        assert "Fürchte dich nicht" in text
        assert quiz.question in text
        assert "#Bibelquiz" in text
        # Referenz sollte NICHT im Quiz-Post stehen
        assert "Jesaja 41,10" not in text

    def test_format_quiz_post_length(self, service, quiz):
        text = service.format_quiz_post(quiz, "Kurzer Vers")
        assert len(text) <= 500

    def test_format_solution_post_basic(self, service, quiz):
        text = service.format_solution_post(quiz)
        assert "Quiz-Auflösung" in text
        assert "Jesaja" in text  # Richtige Antwort
        assert quiz.explanation in text
        assert quiz.losung_reference in text

    def test_format_solution_with_high_score(self, service, quiz):
        poll_results = {
            "votes_count": 100,
            "options": [
                {"votes_count": 10},
                {"votes_count": 10},
                {"votes_count": 75},  # Richtige Antwort
                {"votes_count": 5},
            ],
        }
        text = service.format_solution_post(quiz, poll_results)
        assert "75%" in text
        assert "richtig geantwortet" in text

    def test_format_solution_with_medium_score(self, service, quiz):
        poll_results = {
            "votes_count": 100,
            "options": [
                {"votes_count": 20},
                {"votes_count": 25},
                {"votes_count": 55},  # Richtige Antwort
                {"votes_count": 0},
            ],
        }
        text = service.format_solution_post(quiz, poll_results)
        assert "55%" in text

    def test_format_solution_with_low_score(self, service, quiz):
        poll_results = {
            "votes_count": 100,
            "options": [
                {"votes_count": 40},
                {"votes_count": 30},
                {"votes_count": 20},  # Richtige Antwort
                {"votes_count": 10},
            ],
        }
        text = service.format_solution_post(quiz, poll_results)
        assert "20%" in text

    def test_format_solution_no_votes(self, service, quiz):
        poll_results = {"votes_count": 0, "options": []}
        text = service.format_solution_post(quiz, poll_results)
        # Keine Prozentangabe bei 0 Stimmen
        assert "%" not in text


class TestQuizStateManager:
    """Tests für den Quiz-State-Manager."""

    @pytest.fixture
    def temp_state_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = Path(f.name)
        yield str(path)
        if path.exists():
            path.unlink()

    @pytest.fixture
    def quiz(self):
        return QuizQuestion(
            question="Testfrage",
            options=["A", "B", "C", "D"],
            correct_index=1,
            explanation="Erklärung",
            losung_reference="Test 1,1",
        )

    def test_empty_state_on_init(self, temp_state_file):
        manager = QuizStateManager(temp_state_file)
        assert not manager.has_active_quiz()
        assert manager.get_active_quiz() is None

    def test_save_and_load_quiz(self, temp_state_file, quiz):
        manager = QuizStateManager(temp_state_file)
        manager.save_active_quiz(quiz, "status_123", "poll_456")

        assert manager.has_active_quiz()

        result = manager.get_active_quiz()
        assert result is not None
        loaded_quiz, status_id, poll_id = result
        assert loaded_quiz.question == quiz.question
        assert loaded_quiz.options == quiz.options
        assert loaded_quiz.correct_index == quiz.correct_index
        assert status_id == "status_123"
        assert poll_id == "poll_456"

    def test_persistence_across_instances(self, temp_state_file, quiz):
        manager1 = QuizStateManager(temp_state_file)
        manager1.save_active_quiz(quiz, "status_123", "poll_456")

        # Neuer Manager sollte State laden
        manager2 = QuizStateManager(temp_state_file)
        assert manager2.has_active_quiz()
        result = manager2.get_active_quiz()
        assert result is not None
        assert result[1] == "status_123"

    def test_clear_active_quiz(self, temp_state_file, quiz):
        manager = QuizStateManager(temp_state_file)
        manager.save_active_quiz(quiz, "status_123", "poll_456")
        assert manager.has_active_quiz()

        manager.clear_active_quiz()
        assert not manager.has_active_quiz()
        assert manager.get_active_quiz() is None

    def test_clear_persists(self, temp_state_file, quiz):
        manager1 = QuizStateManager(temp_state_file)
        manager1.save_active_quiz(quiz, "status_123", "poll_456")
        manager1.clear_active_quiz()

        manager2 = QuizStateManager(temp_state_file)
        assert not manager2.has_active_quiz()

    def test_load_corrupted_state(self, temp_state_file):
        # Korrupte JSON-Datei erstellen
        with open(temp_state_file, "w") as f:
            f.write("not valid json {{{")

        manager = QuizStateManager(temp_state_file)
        assert not manager.has_active_quiz()
