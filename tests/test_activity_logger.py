"""Tests für den Activity Logger."""

import csv
import tempfile
from pathlib import Path

from losungs_bot.activity_logger import ActivityLogger, ActivityType


class TestActivityLogger:
    """Tests für den ActivityLogger."""

    def test_creates_csv_file_with_headers(self):
        """Test dass die CSV-Datei mit korrekten Headers erstellt wird."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test_log.csv"
            ActivityLogger(log_file=str(log_file))

            assert log_file.exists()

            with open(log_file, encoding="utf-8") as f:
                reader = csv.reader(f, delimiter=";")
                headers = next(reader)

            assert headers == ["Timestamp", "Aktion", "Beschreibung"]

    def test_log_activity(self):
        """Test dass Aktivitäten korrekt geloggt werden."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test_log.csv"
            logger = ActivityLogger(log_file=str(log_file))

            logger.log(ActivityType.LOSUNG_POSTED, "Test Losungstext")

            with open(log_file, encoding="utf-8") as f:
                reader = csv.reader(f, delimiter=";")
                next(reader)  # Skip headers
                row = next(reader)

            assert len(row) == 3
            assert row[1] == "Losung gepostet"
            assert row[2] == "Test Losungstext"

    def test_log_losung_posted(self):
        """Test log_losung_posted Methode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test_log.csv"
            logger = ActivityLogger(log_file=str(log_file))

            logger.log_losung_posted("Der Herr ist mein Hirte")

            with open(log_file, encoding="utf-8") as f:
                content = f.read()

            assert "Losung gepostet" in content
            assert "Der Herr ist mein Hirte" in content

    def test_log_godi_reminder(self):
        """Test log_godi_reminder Methode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test_log.csv"
            logger = ActivityLogger(log_file=str(log_file))

            logger.log_godi_reminder()

            with open(log_file, encoding="utf-8") as f:
                content = f.read()

            assert "GoDi-Erinnerung gesendet" in content

    def test_log_quiz_started(self):
        """Test log_quiz_started Methode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test_log.csv"
            logger = ActivityLogger(log_file=str(log_file))

            logger.log_quiz_started("Aus welchem Buch stammt dieser Vers?")

            with open(log_file, encoding="utf-8") as f:
                content = f.read()

            assert "Quiz gestartet" in content
            assert "Aus welchem Buch stammt dieser Vers?" in content

    def test_log_quiz_resolved(self):
        """Test log_quiz_resolved Methode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test_log.csv"
            logger = ActivityLogger(log_file=str(log_file))

            logger.log_quiz_resolved(42, "A: 30%, B: 20%, C: 40%, D: 10%")

            with open(log_file, encoding="utf-8") as f:
                content = f.read()

            assert "Quiz aufgelöst" in content
            assert "Teilnehmer: 42" in content
            assert "A: 30%" in content

    def test_log_new_follower(self):
        """Test log_new_follower Methode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test_log.csv"
            logger = ActivityLogger(log_file=str(log_file))

            logger.log_new_follower("test_user@mastodon.social")

            with open(log_file, encoding="utf-8") as f:
                content = f.read()

            assert "Neue Mitglieder" in content
            assert "test_user@mastodon.social" in content

    def test_log_mention_response(self):
        """Test log_mention_response Methode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test_log.csv"
            logger = ActivityLogger(log_file=str(log_file))

            logger.log_mention_response("user@instance.social", "Hilfe gesendet")

            with open(log_file, encoding="utf-8") as f:
                content = f.read()

            assert "Reaktion auf Erwähnungen" in content
            assert "user@instance.social: Hilfe gesendet" in content

    def test_multiple_log_entries(self):
        """Test dass mehrere Einträge korrekt geschrieben werden."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test_log.csv"
            logger = ActivityLogger(log_file=str(log_file))

            logger.log_losung_posted("Losung 1")
            logger.log_godi_reminder()
            logger.log_new_follower("user1")
            logger.log_new_follower("user2")

            with open(log_file, encoding="utf-8") as f:
                reader = csv.reader(f, delimiter=";")
                rows = list(reader)

            # Header + 4 Einträge
            assert len(rows) == 5

    def test_creates_parent_directories(self):
        """Test dass fehlende Verzeichnisse erstellt werden."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "subdir" / "nested" / "test_log.csv"
            ActivityLogger(log_file=str(log_file))

            assert log_file.exists()
            assert log_file.parent.exists()


class TestActivityType:
    """Tests für die ActivityType Enum."""

    def test_all_activity_types_have_german_values(self):
        """Test dass alle Aktivitätstypen deutsche Beschreibungen haben."""
        expected_values = [
            "Losung gepostet",
            "GoDi-Erinnerung gesendet",
            "Quiz gestartet",
            "Quiz aufgelöst",
            "Neue Mitglieder",
            "Reaktion auf Erwähnungen",
        ]

        actual_values = [t.value for t in ActivityType]

        assert sorted(actual_values) == sorted(expected_values)
