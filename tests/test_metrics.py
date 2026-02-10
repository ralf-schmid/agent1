"""Tests für das Prometheus Metrics Modul."""

import json
import tempfile
import time
from pathlib import Path

import pytest

from losungs_bot.metrics import (
    CPU_USAGE_PERCENT,
    FOLLOWERS_COUNT,
    HEALTH_STATUS,
    LIKES_TOTAL,
    MEMORY_USAGE_BYTES,
    MEMORY_USAGE_PERCENT,
    MENTIONS_TOTAL,
    POSTS_TOTAL,
    UPTIME_SECONDS,
    MetricsCollector,
    MetricsServer,
)


@pytest.fixture
def temp_data_dir():
    """Erstellt ein temporäres Verzeichnis für Metriken-State."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def reset_metrics():
    """Setzt alle Metriken vor jedem Test zurück."""
    # Counter können nicht direkt zurückgesetzt werden,
    # aber wir können die _metrics dict leeren
    POSTS_TOTAL._metrics.clear()
    MENTIONS_TOTAL._metrics.clear()
    FOLLOWERS_COUNT._value.set(0)
    LIKES_TOTAL._value.set(0)
    HEALTH_STATUS._value.set(0)
    UPTIME_SECONDS._value.set(0)
    CPU_USAGE_PERCENT._value.set(0)
    MEMORY_USAGE_BYTES._value.set(0)
    MEMORY_USAGE_PERCENT._value.set(0)
    yield


class TestMetricsCollector:
    """Tests für den MetricsCollector."""

    def test_initialization(self, temp_data_dir, reset_metrics):
        """Test dass der Collector korrekt initialisiert wird."""
        MetricsCollector(data_dir=temp_data_dir)

        # Health sollte auf 1 gesetzt sein
        assert HEALTH_STATUS._value.get() == 1

    def test_record_post(self, temp_data_dir, reset_metrics):
        """Test dass Posts korrekt gezählt werden."""
        collector = MetricsCollector(data_dir=temp_data_dir)

        collector.record_post("losung")
        collector.record_post("losung")
        collector.record_post("quiz")

        assert POSTS_TOTAL.labels(type="losung")._value.get() == 2
        assert POSTS_TOTAL.labels(type="quiz")._value.get() == 1

    def test_record_mention(self, temp_data_dir, reset_metrics):
        """Test dass Mentions korrekt gezählt werden."""
        collector = MetricsCollector(data_dir=temp_data_dir)

        collector.record_mention("help")
        collector.record_mention("verse_today")
        collector.record_mention("help")

        assert MENTIONS_TOTAL.labels(command="help")._value.get() == 2
        assert MENTIONS_TOTAL.labels(command="verse_today")._value.get() == 1

    def test_set_followers_count(self, temp_data_dir, reset_metrics):
        """Test dass die Follower-Anzahl korrekt gesetzt wird."""
        collector = MetricsCollector(data_dir=temp_data_dir)

        collector.set_followers_count(42)
        assert FOLLOWERS_COUNT._value.get() == 42

        collector.set_followers_count(100)
        assert FOLLOWERS_COUNT._value.get() == 100

    def test_set_likes_total(self, temp_data_dir, reset_metrics):
        """Test dass die Likes-Anzahl korrekt gesetzt wird."""
        collector = MetricsCollector(data_dir=temp_data_dir)

        collector.set_likes_total(150)
        assert LIKES_TOTAL._value.get() == 150

        collector.set_likes_total(200)
        assert LIKES_TOTAL._value.get() == 200

    def test_set_health_true(self, temp_data_dir, reset_metrics):
        """Test dass Health auf 1 gesetzt wird wenn healthy."""
        collector = MetricsCollector(data_dir=temp_data_dir)

        collector.set_health(True)
        assert HEALTH_STATUS._value.get() == 1

    def test_set_health_false(self, temp_data_dir, reset_metrics):
        """Test dass Health auf 0 gesetzt wird wenn unhealthy."""
        collector = MetricsCollector(data_dir=temp_data_dir)

        collector.set_health(False)
        assert HEALTH_STATUS._value.get() == 0

    def test_update_system_metrics(self, temp_data_dir, reset_metrics):
        """Test dass System-Metriken aktualisiert werden."""
        collector = MetricsCollector(data_dir=temp_data_dir)

        # Kurz warten damit Uptime > 0
        time.sleep(0.1)
        collector.update_system_metrics()

        assert UPTIME_SECONDS._value.get() > 0
        # CPU und Memory sollten >= 0 sein
        assert CPU_USAGE_PERCENT._value.get() >= 0
        assert MEMORY_USAGE_BYTES._value.get() > 0
        assert MEMORY_USAGE_PERCENT._value.get() >= 0


class TestMetricsPersistence:
    """Tests für die Metriken-Persistenz."""

    def test_state_saved_on_record_post(self, temp_data_dir, reset_metrics):
        """Test dass der State nach record_post gespeichert wird."""
        collector = MetricsCollector(data_dir=temp_data_dir)
        state_file = Path(temp_data_dir) / "metrics_state.json"

        collector.record_post("losung")

        assert state_file.exists()
        with open(state_file) as f:
            state = json.load(f)

        assert state["posts"]["losung"] == 1

    def test_state_saved_on_record_mention(self, temp_data_dir, reset_metrics):
        """Test dass der State nach record_mention gespeichert wird."""
        collector = MetricsCollector(data_dir=temp_data_dir)
        state_file = Path(temp_data_dir) / "metrics_state.json"

        collector.record_mention("help")

        assert state_file.exists()
        with open(state_file) as f:
            state = json.load(f)

        assert state["mentions"]["help"] == 1

    def test_state_loaded_on_initialization(self, temp_data_dir, reset_metrics):
        """Test dass der State beim Start geladen wird."""
        state_file = Path(temp_data_dir) / "metrics_state.json"

        # Vorhandenen State erstellen
        state = {
            "posts": {"losung": 10, "quiz": 5},
            "mentions": {"help": 20, "verse_today": 15},
        }
        with open(state_file, "w") as f:
            json.dump(state, f)

        # Collector initialisieren - sollte State laden
        MetricsCollector(data_dir=temp_data_dir)

        assert POSTS_TOTAL.labels(type="losung")._value.get() == 10
        assert POSTS_TOTAL.labels(type="quiz")._value.get() == 5
        assert MENTIONS_TOTAL.labels(command="help")._value.get() == 20
        assert MENTIONS_TOTAL.labels(command="verse_today")._value.get() == 15

    def test_increments_after_state_load(self, temp_data_dir, reset_metrics):
        """Test dass Zähler nach dem Laden korrekt inkrementiert werden."""
        state_file = Path(temp_data_dir) / "metrics_state.json"

        # Vorhandenen State erstellen
        state = {"posts": {"losung": 10}, "mentions": {}}
        with open(state_file, "w") as f:
            json.dump(state, f)

        collector = MetricsCollector(data_dir=temp_data_dir)
        collector.record_post("losung")

        assert POSTS_TOTAL.labels(type="losung")._value.get() == 11

    def test_missing_state_file_handled(self, temp_data_dir, reset_metrics):
        """Test dass fehlende State-Datei korrekt behandelt wird."""
        # Kein State-File erstellen
        collector = MetricsCollector(data_dir=temp_data_dir)

        # Sollte ohne Fehler funktionieren
        collector.record_post("losung")
        assert POSTS_TOTAL.labels(type="losung")._value.get() == 1

    def test_creates_parent_directories(self, temp_data_dir, reset_metrics):
        """Test dass fehlende Verzeichnisse erstellt werden."""
        nested_dir = Path(temp_data_dir) / "subdir" / "nested"
        collector = MetricsCollector(data_dir=str(nested_dir))

        collector.record_post("losung")

        state_file = nested_dir / "metrics_state.json"
        assert state_file.exists()


class TestMetricsServer:
    """Tests für den MetricsServer."""

    def test_server_starts_and_stops(self, temp_data_dir, reset_metrics):
        """Test dass der Server gestartet und gestoppt werden kann."""
        collector = MetricsCollector(data_dir=temp_data_dir)
        server = MetricsServer(port=19999, collector=collector)

        server.start()
        assert server._server is not None
        assert server._thread is not None
        assert server._thread.is_alive()

        server.stop()
        # Thread sollte nach Stop nicht mehr aktiv sein
        time.sleep(0.1)
        assert not server._thread.is_alive()

    def test_server_serves_metrics(self, temp_data_dir, reset_metrics):
        """Test dass der Server Metriken ausliefert."""
        import urllib.request

        collector = MetricsCollector(data_dir=temp_data_dir)
        collector.record_post("losung")
        server = MetricsServer(port=19998, collector=collector)

        try:
            server.start()
            time.sleep(0.1)  # Kurz warten bis Server bereit

            response = urllib.request.urlopen("http://localhost:19998/")
            content = response.read().decode("utf-8")

            assert "losungsbot_posts_total" in content
            assert "losungsbot_health_status" in content
            assert "losungsbot_uptime_seconds" in content
        finally:
            server.stop()


class TestMetricLabels:
    """Tests für Metrik-Labels."""

    def test_post_types(self, temp_data_dir, reset_metrics):
        """Test dass verschiedene Post-Typen korrekt gezählt werden."""
        collector = MetricsCollector(data_dir=temp_data_dir)

        post_types = ["losung", "quiz", "reflection", "church_reminder"]
        for post_type in post_types:
            collector.record_post(post_type)

        for post_type in post_types:
            assert POSTS_TOTAL.labels(type=post_type)._value.get() == 1

    def test_command_labels(self, temp_data_dir, reset_metrics):
        """Test dass verschiedene Commands korrekt gezählt werden."""
        collector = MetricsCollector(data_dir=temp_data_dir)

        commands = ["help", "verse_today", "verse_random", "quiz", "verse_link", "unknown"]
        for command in commands:
            collector.record_mention(command)

        for command in commands:
            assert MENTIONS_TOTAL.labels(command=command)._value.get() == 1
