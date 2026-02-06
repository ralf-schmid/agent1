"""Scheduler für tägliche Losungs-Posts."""

import logging
from collections.abc import Callable
from datetime import datetime
from zoneinfo import ZoneInfo

import structlog
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, EVENT_JOB_MISSED
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = structlog.get_logger()

# APScheduler Logging aktivieren
logging.getLogger("apscheduler").setLevel(logging.DEBUG)


def job_listener(event):
    """Listener für APScheduler Job-Events."""
    if event.exception:
        logger.error(
            "job_failed",
            job_id=event.job_id,
            exception=str(event.exception),
        )
    elif hasattr(event, "job_id"):
        if event.code == EVENT_JOB_MISSED:
            logger.warning(
                "job_missed",
                job_id=event.job_id,
                scheduled_time=str(event.scheduled_run_time),
            )
        else:
            logger.info(
                "job_executed",
                job_id=event.job_id,
            )


class LosungScheduler:
    """Scheduler für das tägliche Posten der Losungen."""

    # Toleranz für verpasste Jobs: 2 Stunden
    # Wenn der Bot innerhalb von 2 Stunden nach der geplanten Zeit startet,
    # wird der Job trotzdem ausgeführt
    MISFIRE_GRACE_TIME = 7200  # 2 Stunden in Sekunden

    def __init__(self, timezone: str = "Europe/Berlin"):
        """
        Initialisiert den Scheduler.

        Args:
            timezone: Zeitzone für das Scheduling (z.B. "Europe/Berlin")
        """
        self.timezone = ZoneInfo(timezone)
        self.scheduler = BlockingScheduler(timezone=self.timezone)

        # Event-Listener für Logging hinzufügen
        self.scheduler.add_listener(
            job_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED,
        )

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
            misfire_grace_time=self.MISFIRE_GRACE_TIME,
        )

        logger.info(
            "daily_job_scheduled",
            hour=hour,
            minute=minute,
            timezone=str(self.timezone),
        )

    def schedule_weekly_job(
        self,
        job_func: Callable,
        day_of_week: int,
        hour: int,
        minute: int,
        job_id: str,
        job_name: str,
    ) -> None:
        """
        Plant einen wöchentlichen Job.

        Args:
            job_func: Die auszuführende Funktion
            day_of_week: Wochentag (0=Montag, 6=Sonntag)
            hour: Stunde (0-23)
            minute: Minute (0-59)
            job_id: Eindeutige Job-ID
            job_name: Anzeigename des Jobs
        """
        trigger = CronTrigger(
            day_of_week=day_of_week,
            hour=hour,
            minute=minute,
            timezone=self.timezone,
        )

        self.scheduler.add_job(
            job_func,
            trigger=trigger,
            id=job_id,
            name=job_name,
            replace_existing=True,
            misfire_grace_time=self.MISFIRE_GRACE_TIME,
        )

        days = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        logger.info(
            "weekly_job_scheduled",
            job_id=job_id,
            day=days[day_of_week],
            hour=hour,
            minute=minute,
        )

    def schedule_interval_job(
        self,
        job_func: Callable,
        seconds: int,
        job_id: str,
        job_name: str,
    ) -> None:
        """
        Plant einen periodischen Job.

        Args:
            job_func: Die auszuführende Funktion
            seconds: Intervall in Sekunden
            job_id: Eindeutige Job-ID
            job_name: Anzeigename des Jobs
        """
        trigger = IntervalTrigger(seconds=seconds)

        self.scheduler.add_job(
            job_func,
            trigger=trigger,
            id=job_id,
            name=job_name,
            replace_existing=True,
        )

        logger.info(
            "interval_job_scheduled",
            job_id=job_id,
            interval_seconds=seconds,
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
        if job is None:
            return None
        # Kompatibilität mit APScheduler v3 und v4
        if hasattr(job, "next_run_time"):
            return job.next_run_time
        return None


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
