"""Haupteinstiegspunkt für den Losungs-Bot."""

import argparse
import logging
import sys

import structlog

from losungs_bot.bible_links import BibleLinkGenerator
from losungs_bot.config import get_settings
from losungs_bot.losungen import LosungenParser
from losungs_bot.mastodon_client import MastodonClient
from losungs_bot.post_formatter import PostFormatter
from losungs_bot.scheduler import LosungScheduler, parse_time


def configure_logging(debug: bool = False) -> None:
    """Konfiguriert das Logging."""
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=log_level)

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

logger = structlog.get_logger()


class LosungsBot:
    """Der Losungs-Bot orchestriert alle Komponenten."""

    def __init__(self):
        self.settings = get_settings()

        # Komponenten initialisieren
        self.losungen_parser = LosungenParser(self.settings.losungen_file)
        self.bible_links = BibleLinkGenerator(
            base_url=self.settings.bible_server_base_url,
            translation=self.settings.bible_translation,
        )
        self.formatter = PostFormatter(self.bible_links)
        self.mastodon = MastodonClient(
            instance_url=self.settings.mastodon_instance,
            access_token=self.settings.mastodon_access_token,
        )

        logger.info("losungs_bot_initialized")

    def post_daily_losung(self) -> bool:
        """Postet die heutige Losung."""
        logger.info("posting_daily_losung")

        # Heutige Losung laden
        losung = self.losungen_parser.get_today()
        if not losung:
            logger.error("no_losung_for_today")
            return False

        # Post formatieren (automatisches Splitting wenn zu lang)
        formatted = self.formatter.format_post(losung)
        main_length = len(formatted.main_post)

        logger.info(
            "post_formatted",
            main_length=main_length,
            needs_reply=formatted.needs_reply,
        )

        # Länge prüfen
        if not self.formatter.validate_length(formatted.main_post):
            logger.error("post_too_long", length=main_length, max=500)
            return False

        # Hauptpost posten
        result = self.mastodon.post_status(formatted.main_post)
        if not result:
            logger.error("losung_post_failed")
            return False

        logger.info("losung_posted_successfully", status_id=result["id"])

        # Copyright-Antwort posten wenn nötig
        if formatted.needs_reply:
            reply_result = self.mastodon.post_status(
                formatted.copyright_reply,
                in_reply_to_id=result["id"],
            )
            if reply_result:
                logger.info(
                    "copyright_reply_posted",
                    reply_id=reply_result["id"],
                    parent_id=result["id"],
                )
            else:
                logger.warning("copyright_reply_failed", parent_id=result["id"])

        return True

    def run_scheduled(self) -> None:
        """Startet den Bot im Scheduled-Modus."""
        from datetime import datetime
        from zoneinfo import ZoneInfo

        tz = ZoneInfo(self.settings.timezone)
        current_time = datetime.now(tz)

        logger.info(
            "starting_scheduled_mode",
            current_time=current_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
        )

        # Credentials prüfen
        if not self.mastodon.verify_credentials():
            logger.error("invalid_mastodon_credentials")
            sys.exit(1)

        # Scheduler einrichten
        scheduler = LosungScheduler(timezone=self.settings.timezone)
        hour, minute = parse_time(self.settings.post_time)

        scheduler.schedule_daily_post(
            job_func=self.post_daily_losung,
            hour=hour,
            minute=minute,
        )

        logger.info(
            "bot_ready",
            post_time=self.settings.post_time,
            timezone=self.settings.timezone,
            misfire_grace_time_hours=scheduler.MISFIRE_GRACE_TIME / 3600,
        )

        # Scheduler starten (blockiert)
        scheduler.start()

    def run_once(self) -> None:
        """Führt einen einzelnen Post aus (für Tests)."""
        logger.info("running_once_mode")

        if not self.mastodon.verify_credentials():
            logger.error("invalid_mastodon_credentials")
            sys.exit(1)

        success = self.post_daily_losung()
        sys.exit(0 if success else 1)

    def dry_run(self) -> None:
        """Zeigt den Post an, ohne ihn zu posten."""
        logger.info("dry_run_mode")

        losung = self.losungen_parser.get_today()
        if not losung:
            print("❌ Keine Losung für heute gefunden!")
            sys.exit(1)

        formatted = self.formatter.format_post(losung)
        main_length = len(formatted.main_post)

        print("\n" + "=" * 50)
        print("📝 VORSCHAU (Dry Run)")
        print("=" * 50)
        print(formatted.main_post)
        print("=" * 50)
        print(f"📏 Länge: {main_length}/500 Zeichen")

        if formatted.needs_reply:
            print("\n" + "-" * 50)
            print("↩️  ANTWORT (Copyright)")
            print("-" * 50)
            print(formatted.copyright_reply)
            print("-" * 50)
            print(f"📏 Länge: {len(formatted.copyright_reply)}/500 Zeichen")

        print("=" * 50 + "\n")


def main() -> None:
    """CLI-Einstiegspunkt."""
    parser = argparse.ArgumentParser(
        description="Losungs-Bot - Tägliche Herrnhuter Losungen im Fediverse"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Führt einen einzelnen Post aus und beendet sich",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Zeigt den Post an, ohne ihn zu posten",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Aktiviert Debug-Logging für detaillierte Ausgaben",
    )

    args = parser.parse_args()

    # Logging konfigurieren
    configure_logging(debug=args.debug)

    bot = LosungsBot()

    if args.dry_run:
        bot.dry_run()
    elif args.once:
        bot.run_once()
    else:
        bot.run_scheduled()


if __name__ == "__main__":
    main()
