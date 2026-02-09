"""Prometheus-Metriken für den Losungs-Bot."""

import threading
import time
from http.server import HTTPServer

import psutil
import structlog
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest
from prometheus_client.core import CollectorRegistry
from prometheus_client.exposition import MetricsHandler

logger = structlog.get_logger()

# Registry für alle Metriken
REGISTRY = CollectorRegistry()

# Metriken definieren
POSTS_TOTAL = Counter(
    "losungsbot_posts_total",
    "Gesamtanzahl der geposteten Nachrichten",
    ["type"],  # losung, quiz, reflection, church_reminder
    registry=REGISTRY,
)

FOLLOWERS_COUNT = Gauge(
    "losungsbot_followers_count",
    "Aktuelle Anzahl der Follower",
    registry=REGISTRY,
)

MENTIONS_TOTAL = Counter(
    "losungsbot_mentions_total",
    "Gesamtanzahl der verarbeiteten Erwähnungen",
    ["command"],  # help, verse_today, verse_random, quiz, verse_link, unknown
    registry=REGISTRY,
)

UPTIME_SECONDS = Gauge(
    "losungsbot_uptime_seconds",
    "Uptime des Bots in Sekunden",
    registry=REGISTRY,
)

CPU_USAGE_PERCENT = Gauge(
    "losungsbot_cpu_usage_percent",
    "CPU-Auslastung in Prozent",
    registry=REGISTRY,
)

MEMORY_USAGE_BYTES = Gauge(
    "losungsbot_memory_usage_bytes",
    "RAM-Nutzung in Bytes",
    registry=REGISTRY,
)

MEMORY_USAGE_PERCENT = Gauge(
    "losungsbot_memory_usage_percent",
    "RAM-Nutzung in Prozent",
    registry=REGISTRY,
)


class MetricsCollector:
    """Sammelt und aktualisiert Prometheus-Metriken."""

    def __init__(self):
        """Initialisiert den Metrics Collector."""
        self._start_time = time.time()
        self._process = psutil.Process()
        logger.info("metrics_collector_initialized")

    def update_system_metrics(self) -> None:
        """Aktualisiert System-Metriken (CPU, RAM, Uptime)."""
        # Uptime
        uptime = time.time() - self._start_time
        UPTIME_SECONDS.set(uptime)

        # CPU (Prozess-spezifisch)
        try:
            cpu_percent = self._process.cpu_percent(interval=None)
            CPU_USAGE_PERCENT.set(cpu_percent)
        except Exception:
            pass

        # RAM (Prozess-spezifisch)
        try:
            memory_info = self._process.memory_info()
            MEMORY_USAGE_BYTES.set(memory_info.rss)
            MEMORY_USAGE_PERCENT.set(self._process.memory_percent())
        except Exception:
            pass

    def record_post(self, post_type: str) -> None:
        """
        Zeichnet einen geposteten Beitrag auf.

        Args:
            post_type: Art des Posts (losung, quiz, reflection, church_reminder)
        """
        POSTS_TOTAL.labels(type=post_type).inc()
        logger.debug("metric_post_recorded", type=post_type)

    def record_mention(self, command: str) -> None:
        """
        Zeichnet eine verarbeitete Erwähnung auf.

        Args:
            command: Erkannter Befehl (help, verse_today, verse_random, quiz, verse_link, unknown)
        """
        MENTIONS_TOTAL.labels(command=command).inc()
        logger.debug("metric_mention_recorded", command=command)

    def set_followers_count(self, count: int) -> None:
        """
        Setzt die aktuelle Follower-Anzahl.

        Args:
            count: Anzahl der Follower
        """
        FOLLOWERS_COUNT.set(count)
        logger.debug("metric_followers_updated", count=count)


class MetricsServer:
    """HTTP-Server für Prometheus-Metriken."""

    def __init__(self, port: int = 80, collector: MetricsCollector | None = None):
        """
        Initialisiert den Metrics Server.

        Args:
            port: HTTP-Port für den Metrics-Endpoint
            collector: MetricsCollector für System-Metriken Updates
        """
        self.port = port
        self.collector = collector
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None

    def _create_handler(self):
        """Erstellt einen Handler mit System-Metriken-Update."""
        collector = self.collector

        class CustomMetricsHandler(MetricsHandler):
            def do_GET(self):
                # System-Metriken vor jeder Abfrage aktualisieren
                if collector:
                    collector.update_system_metrics()

                # Metriken generieren
                self.send_response(200)
                self.send_header("Content-Type", CONTENT_TYPE_LATEST)
                self.end_headers()
                self.wfile.write(generate_latest(REGISTRY))

        return CustomMetricsHandler

    def start(self) -> None:
        """Startet den Metrics-Server in einem separaten Thread."""
        handler = self._create_handler()
        self._server = HTTPServer(("0.0.0.0", self.port), handler)

        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

        logger.info("metrics_server_started", port=self.port)

    def stop(self) -> None:
        """Stoppt den Metrics-Server."""
        if self._server:
            self._server.shutdown()
            logger.info("metrics_server_stopped")


# Globale Instanzen für einfachen Zugriff
_collector: MetricsCollector | None = None
_server: MetricsServer | None = None


def get_collector() -> MetricsCollector:
    """Gibt den globalen MetricsCollector zurück (lazy initialization)."""
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector


def start_metrics_server(port: int = 80) -> MetricsServer:
    """
    Startet den globalen Metrics-Server.

    Args:
        port: HTTP-Port für den Metrics-Endpoint

    Returns:
        MetricsServer Instanz
    """
    global _server
    if _server is None:
        _server = MetricsServer(port=port, collector=get_collector())
        _server.start()
    return _server


def stop_metrics_server() -> None:
    """Stoppt den globalen Metrics-Server."""
    global _server
    if _server:
        _server.stop()
        _server = None
