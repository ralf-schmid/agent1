"""Scheduler für tägliche Losungs-Posts."""

from collections.abc import Callable
from datetime import datetime
from zoneinfo import ZoneInfo

import structlog
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

logger = structlog.get_logger()


class LosungScheduler:
    """Scheduler für das tägliche Posten der Losungen."""

    def __init__(self, timezone: str = "Europe/Berlin"):
        """
        Initialisiert den Scheduler.

        Args:
            timezone: Zeitzone für das Scheduling (z.B. "Europe/Berlin")
        """
        self.timezone = ZoneInfo(timezone)
        self.scheduler = BlockingScheduler(timezone=self.timezone)
        logger.info("scheduler_initialized", timezone=timezone)

    def schedule_daily_post(
        self,
        job_func: Callable,
        hour: int = 6,
        minute: int = 0,
    ) -> None:
        """
        Plant einen täglichen Job.

        Args:
            job_func: Die auszuführende Funktion
            hour: Stunde (0-23)
            minute: Minute (0-59)
        """
        trigger = CronTrigger(
            hour=hour,
            minute=minute,
            timezone=self.timezone,
        )

        self.scheduler.add_job(
            job_func,
            trigger=trigger,
            id="daily_losung_post",
            name="Tägliche Losung posten",
            replace_existing=True,
        )

        next_run = self.scheduler.get_job("daily_losung_post").next_run_time
        logger.info(
            "daily_job_scheduled",
            hour=hour,
            minute=minute,
            next_run=next_run.isoformat() if next_run else None,
        )

    def run_now(self, job_func: Callable) -> None:
        """Führt einen Job sofort aus (für Tests)."""
        logger.info("running_job_immediately")
        job_func()

    def start(self) -> None:
        """Startet den Scheduler (blockiert)."""
        logger.info("scheduler_starting")
        try:
            self.scheduler.start()
        except KeyboardInterrupt:
            logger.info("scheduler_stopped_by_user")
            self.scheduler.shutdown()

    def get_next_run_time(self) -> datetime | None:
        """Gibt den nächsten geplanten Ausführungszeitpunkt zurück."""
        job = self.scheduler.get_job("daily_losung_post")
        return job.next_run_time if job else None


def parse_time(time_str: str) -> tuple[int, int]:
    """
    Parst einen Zeit-String im Format "HH:MM".

    Args:
        time_str: Zeit im Format "06:00" oder "6:00"

    Returns:
        Tuple (hour, minute)
    """
    parts = time_str.split(":")
    hour = int(parts[0])
    minute = int(parts[1]) if len(parts) > 1 else 0
    return hour, minute
