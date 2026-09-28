"""Tests für den Quiz-Ablauf im LosungsBot."""

from unittest.mock import MagicMock

from losungs_bot.ai_client import AIClient
from losungs_bot.main import LosungsBot


def _make_bot(has_active_quiz: bool) -> LosungsBot:
    bot = LosungsBot.__new__(LosungsBot)
    bot.quiz_service = MagicMock()
    bot.quiz_state = MagicMock()
    bot.quiz_state.has_active_quiz.return_value = has_active_quiz
    bot.losungen_parser = MagicMock()
    bot.losungen_parser.get_today.return_value = None  # Abbruch nach dem State-Check
    return bot


def test_default_model_is_not_retired():
    """claude-3-haiku-20240307 wurde am 19.04.2026 abgeschaltet."""
    assert AIClient.DEFAULT_MODEL == "claude-haiku-4-5"


def test_stale_quiz_is_resolved_before_new_quiz():
    bot = _make_bot(has_active_quiz=True)
    bot.post_quiz_solution = MagicMock(return_value=True)

    bot.post_quiz()

    bot.post_quiz_solution.assert_called_once()
    bot.quiz_state.clear_active_quiz.assert_not_called()
    bot.losungen_parser.get_today.assert_called_once()


def test_stale_quiz_is_discarded_if_solution_fails():
    bot = _make_bot(has_active_quiz=True)
    bot.post_quiz_solution = MagicMock(return_value=False)

    bot.post_quiz()

    bot.quiz_state.clear_active_quiz.assert_called_once()
    bot.losungen_parser.get_today.assert_called_once()


def test_no_active_quiz_skips_solution():
    bot = _make_bot(has_active_quiz=False)
    bot.post_quiz_solution = MagicMock()

    bot.post_quiz()

    bot.post_quiz_solution.assert_not_called()
    bot.losungen_parser.get_today.assert_called_once()
