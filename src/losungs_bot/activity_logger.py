"""CSV-basiertes Aktivitäts-Logging für den Bot."""

import csv
from datetime import datetime
from enum import Enum
from pathlib import Path
from zoneinfo import ZoneInfo

import structlog

logger = structlog.get_logger()


class ActivityType(Enum):
    """Typen von Bot-Aktivitäten."""

    LOSUNG_POSTED = "Losung gepostet"
    GODI_REMINDER = "GoDi-Erinnerung gesendet"
    QUIZ_STARTED = "Quiz gestartet"
    QUIZ_RESOLVED = "Quiz aufgelöst"
    NEW_FOLLOWER = "Neue Mitglieder"
    MENTION_RESPONSE = "Reaktion auf Erwähnungen"


class ActivityLogger:
    """Loggt Bot-Aktivitäten in eine CSV-Datei."""

    CSV_HEADERS = ["Timestamp", "Aktion", "Beschreibung"]
    CSV_DELIMITER = ";"

    def __init__(
        self,
        log_file: str = "data/activity_log.csv",
        timezone: str = "Europe/Berlin",
    ):
        """
        Initialisiert den Activity Logger.

        Args:
            log_file: Pfad zur CSV-Datei
            timezone: Zeitzone für Timestamps
        """
        self.log_file = Path(log_file)
        self.timezone = ZoneInfo(timezone)
        self._ensure_file_exists()
        logger.info("activity_logger_initialized", log_file=str(self.log_file))

    def _ensure_file_exists(self) -> None:
        """Stellt sicher, dass die CSV-Datei mit Header existiert."""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        if not self.log_file.exists():
            with open(self.log_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=self.CSV_DELIMITER)
                writer.writerow(self.CSV_HEADERS)
            logger.info("activity_log_created", path=str(self.log_file))

    def _get_timestamp(self) -> str:
        """Gibt den aktuellen Timestamp formatiert zurück."""
        return datetime.now(self.timezone).strftime("%Y-%m-%d %H:%M:%S")

    def _sanitize_csv_value(self, value: str) -> str:
        """
        Sanitiert einen Wert gegen CSV Injection.

        Verhindert, dass Werte die mit =, +, -, @, Tab oder CR beginnen
        in Tabellenkalkulationen als Formeln interpretiert werden.

        Args:
            value: Der zu sanitierende Wert

        Returns:
            Sanitierter Wert (mit führendem Apostroph wenn nötig)
        """
        if value and value[0] in ("=", "+", "-", "@", "\t", "\r"):
            return f"'{value}"
        return value

    def log(self, activity_type: ActivityType, description: str) -> None:
        """
        Loggt eine Aktivität in die CSV-Datei.

        Args:
            activity_type: Art der Aktivität
            description: Beschreibung der Aktivität
        """
        timestamp = self._get_timestamp()
        # Beschreibung sanitieren gegen CSV Injection
        safe_description = self._sanitize_csv_value(description)
        row = [timestamp, activity_type.value, safe_description]

        try:
            with open(self.log_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=self.CSV_DELIMITER)
                writer.writerow(row)

            logger.debug(
                "activity_logged",
                activity=activity_type.value,
                description=description[:50],
            )
        except OSError as e:
            logger.error("activity_log_failed", error=str(e))

    def log_losung_posted(self, losung_text: str) -> None:
        """Loggt eine gepostete Losung."""
        self.log(ActivityType.LOSUNG_POSTED, losung_text)

    def log_godi_reminder(self) -> None:
        """Loggt eine gesendete GoDi-Erinnerung."""
        self.log(ActivityType.GODI_REMINDER, "Gottesdienst-Erinnerung gesendet")

    def log_quiz_started(self, question: str) -> None:
        """Loggt ein gestartetes Quiz."""
        self.log(ActivityType.QUIZ_STARTED, question)

    def log_quiz_resolved(
        self,
        participants: int,
        results_distribution: str,
    ) -> None:
        """
        Loggt eine Quiz-Auflösung.

        Args:
            participants: Anzahl der Teilnehmer
            results_distribution: Verteilung der Antworten (z.B. "A: 30%, B: 20%, C: 40%, D: 10%")
        """
        description = f"Teilnehmer: {participants}, Verteilung: {results_distribution}"
        self.log(ActivityType.QUIZ_RESOLVED, description)

    def log_new_follower(self, account_name: str) -> None:
        """Loggt einen neuen Follower."""
        self.log(ActivityType.NEW_FOLLOWER, account_name)

    def log_mention_response(self, account_name: str, reaction: str) -> None:
        """
        Loggt eine Reaktion auf eine Erwähnung.

        Args:
            account_name: Name des erwähnenden Accounts
            reaction: Art der Reaktion (z.B. "Hilfe gesendet", "Losung gesendet")
        """
        description = f"{account_name}: {reaction}"
        self.log(ActivityType.MENTION_RESPONSE, description)
