"""Haupteinstiegspunkt für den Losungs-Bot."""

import argparse
import logging
import sys

import structlog

from losungs_bot.activity_logger import ActivityLogger
from losungs_bot.ai_client import AIClient
from losungs_bot.bible_links import BibleLinkGenerator
from losungs_bot.church_service import ChurchServiceReminder
from losungs_bot.config import get_settings
from losungs_bot.follower_manager import FollowerManager
from losungs_bot.losungen import LosungenParser
from losungs_bot.mastodon_client import MastodonClient
from losungs_bot.mention_handler import MentionHandler
from losungs_bot.metrics import get_collector, start_metrics_server
from losungs_bot.post_formatter import PostFormatter
from losungs_bot.quiz_service import QuizService, QuizStateManager
from losungs_bot.reflection_service import ReflectionService
from losungs_bot.repost_service import RepostService
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
        self.formatter = PostFormatter(
            self.bible_links,
            podcast_apple=self.settings.podcast_apple,
            podcast_spotify=self.settings.podcast_spotify,
        )
        self.mastodon = MastodonClient(
            instance_url=self.settings.mastodon_instance,
            access_token=self.settings.mastodon_access_token,
        )

        # Optionale Komponenten
        self.church_reminder = None
        self.follower_manager = None
        self.quiz_service = None
        self.quiz_state = None
        self.reflection_service = None
        self.mention_handler = None
        self.repost_service = None

        # Gemeinsamer AI-Client (wird bei Bedarf initialisiert)
        self._ai_client: AIClient | None = None

        # Separate Notification-IDs für verschiedene Typen
        self._last_mention_id: str | None = None
        self._last_favorite_id: str | None = None

        # Activity Logger für CSV-Protokollierung
        self.activity_logger = ActivityLogger(timezone=self.settings.timezone)

        # Metriken-Collector
        self.metrics = get_collector()

        logger.info("losungs_bot_initialized")

    def _get_ai_client(self) -> AIClient | None:
        """Gibt den gemeinsamen AI-Client zurück (Lazy Init)."""
        if self._ai_client is None and self.settings.anthropic_api_key:
            self._ai_client = AIClient(self.settings.anthropic_api_key)
        return self._ai_client

    def _init_church_reminder(self) -> None:
        """Initialisiert die Gottesdienst-Erinnerung."""
        if self.settings.church_reminder_enabled:
            self.church_reminder = ChurchServiceReminder()
            logger.info("church_reminder_enabled")

    def _init_follower_manager(self) -> None:
        """Initialisiert den Follower-Manager."""
        if self.settings.auto_follow_back or self.settings.welcome_message_enabled:
            self.follower_manager = FollowerManager(
                client=self.mastodon._client,
                state_file=self.settings.follower_state_file,
                notify_account=self.settings.admin_notify_account,
                activity_logger=self.activity_logger,
            )
            # Beim ersten Start: bestehende Follower initialisieren
            self.follower_manager.initialize_known_followers()
            logger.info(
                "follower_manager_enabled",
                auto_follow=self.settings.auto_follow_back,
                welcome_msg=self.settings.welcome_message_enabled,
                notify_account=self.settings.admin_notify_account,
            )

    def _init_quiz_service(self) -> None:
        """Initialisiert den Quiz-Service."""
        if self.settings.quiz_enabled and self.settings.anthropic_api_key:
            ai_client = self._get_ai_client()
            self.quiz_service = QuizService(ai_client=ai_client)
            self.quiz_state = QuizStateManager(
                state_file=self.settings.quiz_state_file
            )
            logger.info(
                "quiz_service_enabled",
                quiz_day=self.settings.quiz_day,
                quiz_time=self.settings.quiz_time,
            )
        elif self.settings.quiz_enabled and not self.settings.anthropic_api_key:
            logger.warning("quiz_enabled_but_no_api_key")

    def _init_reflection_service(self) -> None:
        """Initialisiert den Reflexions-Service."""
        if self.settings.reflection_enabled and self.settings.anthropic_api_key:
            ai_client = self._get_ai_client()
            self.reflection_service = ReflectionService(ai_client=ai_client)
            logger.info(
                "reflection_service_enabled",
                reflection_time=self.settings.reflection_time,
            )
        elif self.settings.reflection_enabled and not self.settings.anthropic_api_key:
            logger.warning("reflection_enabled_but_no_api_key")

    def _init_mention_handler(self) -> None:
        """Initialisiert den Mention-Handler."""
        if self.settings.mentions_enabled:
            self.mention_handler = MentionHandler(
                mastodon_client=self.mastodon,
                losungen_parser=self.losungen_parser,
                bible_links=self.bible_links,
                quiz_service=self.quiz_service,
                activity_logger=self.activity_logger,
                metrics_collector=self.metrics,
            )
            logger.info("mention_handler_enabled")

    def _init_repost_service(self) -> None:
        """Initialisiert den Repost-Service."""
        if self.settings.repost_enabled and self.settings.repost_accounts:
            accounts = [
                a.strip()
                for a in self.settings.repost_accounts.split(",")
                if a.strip()
            ]
            if accounts:
                self.repost_service = RepostService(
                    mastodon_client=self.mastodon,
                    accounts=accounts,
                )
                logger.info(
                    "repost_service_enabled",
                    accounts=accounts,
                    repost_time=self.settings.repost_time,
                )

    def run_repost(self) -> int:
        """Führt das automatische Reposten aus."""
        if not self.repost_service:
            logger.warning("repost_service_not_initialized")
            return 0

        logger.info("running_repost")
        count = self.repost_service.repost_recent_statuses(hours=24)
        logger.info("repost_completed", boosted_count=count)
        return count

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

        # Aktivität loggen
        self.activity_logger.log_losung_posted(losung.losungstext)
        self.metrics.record_post("losung")

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

    def post_church_reminder(self) -> bool:
        """Postet die Gottesdienst-Erinnerung."""
        if not self.church_reminder:
            logger.warning("church_reminder_not_initialized")
            return False

        logger.info("posting_church_reminder")

        reminder_text = self.church_reminder.format_saturday_reminder()

        result = self.mastodon.post_status(reminder_text)
        if result:
            logger.info("church_reminder_posted", status_id=result["id"])
            self.activity_logger.log_godi_reminder()
            self.metrics.record_post("church_reminder")
            return True

        logger.error("church_reminder_failed")
        return False

    def check_followers(self) -> None:
        """Prüft auf neue Follower und verarbeitet sie."""
        if not self.follower_manager:
            return

        count = self.follower_manager.process_new_followers()
        if count > 0:
            logger.info("new_followers_processed", count=count)

        # Metriken aktualisieren (Follower und Likes)
        try:
            me = self.mastodon._client.me()
            self.metrics.set_followers_count(me.get("followers_count", 0))
            self.metrics.set_likes_total(self.mastodon.get_total_likes())
        except Exception:
            pass

    def post_quiz(self) -> bool:
        """Postet ein neues Quiz basierend auf der Tageslosung."""
        if not self.quiz_service or not self.quiz_state:
            logger.warning("quiz_service_not_initialized")
            return False

        # Prüfen ob noch ein Quiz aktiv ist
        if self.quiz_state.has_active_quiz():
            logger.warning("quiz_already_active")
            return False

        logger.info("generating_quiz")

        # Tageslosung laden
        losung = self.losungen_parser.get_today()
        if not losung:
            logger.error("no_losung_for_quiz")
            return False

        # Quiz generieren
        quiz = self.quiz_service.generate_quiz(losung)
        if not quiz:
            logger.error("quiz_generation_failed")
            return False

        # Quiz-Post formatieren
        post_text = self.quiz_service.format_quiz_post(quiz, losung.losungstext)

        # Poll posten
        result = self.mastodon.post_poll(
            content=post_text,
            options=quiz.options,
            expires_in=self.settings.quiz_poll_duration,
        )

        if not result:
            logger.error("quiz_post_failed")
            return False

        # Status und Poll-ID speichern
        poll_id = result.get("poll", {}).get("id")
        if poll_id:
            self.quiz_state.save_active_quiz(
                quiz=quiz,
                status_id=str(result["id"]),
                poll_id=str(poll_id),
            )
            logger.info(
                "quiz_posted",
                status_id=result["id"],
                poll_id=poll_id,
            )
            self.activity_logger.log_quiz_started(quiz.question)
            self.metrics.record_post("quiz")
            return True

        logger.error("quiz_no_poll_id")
        return False

    def post_quiz_solution(self) -> bool:
        """Postet die Auflösung des aktiven Quiz."""
        if not self.quiz_service or not self.quiz_state:
            logger.warning("quiz_service_not_initialized")
            return False

        # Aktives Quiz laden
        active = self.quiz_state.get_active_quiz()
        if not active:
            logger.info("no_active_quiz_for_solution")
            return False

        quiz, status_id, poll_id = active
        logger.info("posting_quiz_solution", poll_id=poll_id)

        # Poll-Ergebnisse abrufen
        poll_results = self.mastodon.get_poll(poll_id)

        # Auflösung formatieren
        solution_text = self.quiz_service.format_solution_post(quiz, poll_results)

        # Als Antwort auf den Quiz-Post posten
        result = self.mastodon.post_status(
            content=solution_text,
            in_reply_to_id=status_id,
        )

        if result:
            logger.info("quiz_solution_posted", status_id=result["id"])
            self.quiz_state.clear_active_quiz()

            # Aktivität loggen
            participants = 0
            distribution = "N/A"
            if poll_results and poll_results.get("votes_count", 0) > 0:
                participants = poll_results["votes_count"]
                options = poll_results.get("options", [])
                dist_parts = []
                for i, opt in enumerate(options):
                    votes = opt.get("votes_count", 0)
                    pct = round(votes / participants * 100) if participants > 0 else 0
                    label = chr(65 + i)  # A, B, C, D
                    dist_parts.append(f"{label}: {pct}%")
                distribution = ", ".join(dist_parts)
            self.activity_logger.log_quiz_resolved(participants, distribution)

            return True

        logger.error("quiz_solution_failed")
        return False

    def post_reflection(self) -> bool:
        """Postet die tägliche Reflexionsfrage."""
        if not self.reflection_service:
            logger.warning("reflection_service_not_initialized")
            return False

        logger.info("posting_reflection")

        losung = self.losungen_parser.get_today()
        if not losung:
            logger.error("no_losung_for_reflection")
            return False

        question = self.reflection_service.generate_reflection(losung)
        if not question:
            logger.error("reflection_generation_failed")
            return False

        post_text = self.reflection_service.format_reflection_post(losung, question)

        result = self.mastodon.post_status(post_text)
        if result:
            logger.info("reflection_posted", status_id=result["id"])
            self.metrics.record_post("reflection")
            return True

        logger.error("reflection_post_failed")
        return False

    def process_mentions(self) -> None:
        """Verarbeitet neue Erwähnungen."""
        if not self.mention_handler:
            return

        # Erwähnungen abrufen
        notifications = self.mastodon.get_notifications(
            types=["mention"],
            since_id=self._last_mention_id,
            limit=20,
        )

        if not notifications:
            return

        # Neueste ID speichern
        self._last_mention_id = str(notifications[0]["id"])

        for notification in reversed(notifications):  # Älteste zuerst
            try:
                self.mention_handler.process_mention(notification)
                self.mastodon.dismiss_notification(str(notification["id"]))
            except Exception as e:
                logger.error(
                    "mention_processing_failed",
                    notification_id=notification["id"],
                    error=str(e),
                )

        logger.info("mentions_processed", count=len(notifications))

    def process_favorites(self) -> None:
        """Reagiert auf neue Favoriten mit einer DM."""
        if not self.settings.favorites_reaction_enabled:
            return

        notifications = self.mastodon.get_notifications(
            types=["favourite"],
            since_id=self._last_favorite_id,
            limit=20,
        )

        if not notifications:
            return

        # Neueste ID speichern
        self._last_favorite_id = str(notifications[0]["id"])

        for notification in notifications:
            account = notification.get("account", {})
            username = account.get("acct", "")

            if username:
                self.mastodon.send_direct_message(
                    username=username,
                    content="Danke für dein ❤️! Schön, dass dir der Beitrag gefällt. "
                    "Schreib mir 'hilfe' wenn du wissen möchtest, was ich alles kann. 🙏",
                )
                self.mastodon.dismiss_notification(str(notification["id"]))

        logger.info("favorites_processed", count=len(notifications))

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

        # Metrics-Server starten
        if self.settings.metrics_enabled:
            start_metrics_server(port=self.settings.metrics_port)
            # Initial Metriken setzen
            try:
                me = self.mastodon._client.me()
                self.metrics.set_followers_count(me.get("followers_count", 0))
                self.metrics.set_likes_total(self.mastodon.get_total_likes())
            except Exception:
                pass

        # Optionale Komponenten initialisieren
        self._init_church_reminder()
        self._init_follower_manager()
        self._init_quiz_service()
        self._init_reflection_service()
        self._init_mention_handler()
        self._init_repost_service()

        # Scheduler einrichten
        scheduler = LosungScheduler(timezone=self.settings.timezone)
        hour, minute = parse_time(self.settings.post_time)

        # Tägliche Losung
        scheduler.schedule_daily_post(
            job_func=self.post_daily_losung,
            hour=hour,
            minute=minute,
        )

        # Gottesdienst-Erinnerung (Samstag)
        if self.settings.church_reminder_enabled:
            church_hour, church_minute = parse_time(self.settings.church_reminder_time)
            scheduler.schedule_weekly_job(
                job_func=self.post_church_reminder,
                day_of_week=self.settings.church_reminder_day,
                hour=church_hour,
                minute=church_minute,
                job_id="church_reminder",
                job_name="Gottesdienst-Erinnerung",
            )

        # Follower-Check (täglich)
        if self.follower_manager:
            follower_hour, follower_minute = parse_time(self.settings.follower_check_time)
            scheduler.schedule_daily_post(
                job_func=self.check_followers,
                hour=follower_hour,
                minute=follower_minute,
                job_id="follower_check",
            )

        # Bibelquiz (wöchentlich)
        if self.quiz_service:
            quiz_hour, quiz_minute = parse_time(self.settings.quiz_time)
            # Quiz posten
            scheduler.schedule_weekly_job(
                job_func=self.post_quiz,
                day_of_week=self.settings.quiz_day,
                hour=quiz_hour,
                minute=quiz_minute,
                job_id="bible_quiz",
                job_name="Bibelquiz",
            )
            # Quiz-Auflösung (nächster Tag, gleiche Uhrzeit)
            solution_day = (self.settings.quiz_day + 1) % 7
            scheduler.schedule_weekly_job(
                job_func=self.post_quiz_solution,
                day_of_week=solution_day,
                hour=quiz_hour,
                minute=quiz_minute,
                job_id="quiz_solution",
                job_name="Quiz-Auflösung",
            )

        # Reflexionsfrage (täglich)
        if self.reflection_service:
            reflection_hour, reflection_minute = parse_time(
                self.settings.reflection_time
            )
            scheduler.schedule_daily_post(
                job_func=self.post_reflection,
                hour=reflection_hour,
                minute=reflection_minute,
                job_id="daily_reflection",
            )

        # Mentions-Check (alle X Sekunden)
        if self.mention_handler:
            scheduler.schedule_interval_job(
                job_func=self.process_mentions,
                seconds=self.settings.mentions_check_interval,
                job_id="mentions_check",
                job_name="Erwähnungen prüfen",
            )

        # Repost/Boost (täglich)
        if self.repost_service:
            repost_hour, repost_minute = parse_time(self.settings.repost_time)
            scheduler.schedule_daily_post(
                job_func=self.run_repost,
                hour=repost_hour,
                minute=repost_minute,
                job_id="daily_repost",
            )

        logger.info(
            "bot_ready",
            post_time=self.settings.post_time,
            timezone=self.settings.timezone,
            misfire_grace_time_hours=scheduler.MISFIRE_GRACE_TIME / 3600,
            church_reminder=self.settings.church_reminder_enabled,
            follower_features=self.follower_manager is not None,
            quiz_enabled=self.quiz_service is not None,
            reflection_enabled=self.reflection_service is not None,
            mentions_enabled=self.mention_handler is not None,
            repost_enabled=self.repost_service is not None,
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
        print("📝 VORSCHAU - Tägliche Losung")
        print("=" * 50)
        print(formatted.main_post)
        print("=" * 50)
        print(f"📏 Länge: {main_length}/500 Zeichen")

        if formatted.needs_reply:
            print("\n" + "-" * 50)
            print("↩️  ANTWORT (Copyright + Podcast)")
            print("-" * 50)
            print(formatted.copyright_reply)
            print("-" * 50)
            print(f"📏 Länge: {len(formatted.copyright_reply)}/500 Zeichen")

        # Gottesdienst-Vorschau
        if self.settings.church_reminder_enabled:
            self._init_church_reminder()
            print("\n" + "=" * 50)
            print("⛪ VORSCHAU - Gottesdienst-Erinnerung (Samstag)")
            print("=" * 50)
            reminder = self.church_reminder.format_saturday_reminder()
            print(reminder)
            print("=" * 50)
            print(f"📏 Länge: {len(reminder)}/500 Zeichen")

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
    parser.add_argument(
        "--init-followers",
        action="store_true",
        help="Initialisiert die Liste bekannter Follower (ohne Nachrichten)",
    )
    parser.add_argument(
        "--church-reminder",
        action="store_true",
        help="Postet die Gottesdienst-Erinnerung sofort",
    )
    parser.add_argument(
        "--test-welcome",
        action="store_true",
        help="Sendet Test-Willkommensnachricht an den Admin-Account",
    )
    parser.add_argument(
        "--test-quiz",
        action="store_true",
        help="Postet ein Bibelquiz sofort (benötigt ANTHROPIC_API_KEY)",
    )
    parser.add_argument(
        "--quiz-solution",
        action="store_true",
        help="Postet die Auflösung des aktiven Quiz",
    )
    parser.add_argument(
        "--dry-run-quiz",
        action="store_true",
        help="Generiert ein Quiz und zeigt es an, ohne zu posten",
    )
    parser.add_argument(
        "--repost",
        action="store_true",
        help="Führt das Reposten/Boosten sofort aus",
    )
    parser.add_argument(
        "--dry-run-repost",
        action="store_true",
        help="Zeigt an, welche Beiträge geboosted würden, ohne zu boosten",
    )

    args = parser.parse_args()

    # Logging konfigurieren
    configure_logging(debug=args.debug)

    bot = LosungsBot()

    if args.test_welcome:
        if not bot.mastodon.verify_credentials():
            logger.error("invalid_mastodon_credentials")
            sys.exit(1)
        admin = bot.settings.admin_notify_account
        if not admin:
            print("❌ ADMIN_NOTIFY_ACCOUNT nicht konfiguriert!")
            sys.exit(1)
        # Sende Willkommensnachricht an Admin
        bot._init_follower_manager()
        # Fake-Account für den Admin erstellen
        test_account = {"acct": admin, "id": "test"}
        success = bot.follower_manager.send_welcome_message(test_account)
        if success:
            print(f"✅ Test-Willkommensnachricht an @{admin} gesendet")
        else:
            print("❌ Fehler beim Senden der Nachricht")
        sys.exit(0 if success else 1)
    elif args.init_followers:
        if not bot.mastodon.verify_credentials():
            logger.error("invalid_mastodon_credentials")
            sys.exit(1)
        bot._init_follower_manager()
        print("✅ Follower initialisiert")
    elif args.church_reminder:
        if not bot.mastodon.verify_credentials():
            logger.error("invalid_mastodon_credentials")
            sys.exit(1)
        bot._init_church_reminder()
        success = bot.post_church_reminder()
        sys.exit(0 if success else 1)
    elif args.dry_run_quiz:
        if not bot.settings.anthropic_api_key:
            print("❌ ANTHROPIC_API_KEY nicht konfiguriert!")
            sys.exit(1)

        print("\n" + "=" * 50)
        print("📖 VORSCHAU - Bibelquiz")
        print("=" * 50)

        losung = bot.losungen_parser.get_today()
        if not losung:
            print("❌ Keine Losung für heute gefunden!")
            sys.exit(1)

        print(f"\n📜 Tageslosung: {losung.losungsvers}")
        print(f'   "{losung.losungstext}"\n')
        print("-" * 50)
        print("⏳ Generiere Quiz mit Claude...")

        ai_client = bot._get_ai_client()
        quiz_service = QuizService(ai_client=ai_client)
        quiz = quiz_service.generate_quiz(losung)

        if not quiz:
            print("❌ Quiz-Generierung fehlgeschlagen!")
            sys.exit(1)

        post_text = quiz_service.format_quiz_post(quiz, losung.losungstext)
        solution_text = quiz_service.format_solution_post(quiz)

        print("\n" + "=" * 50)
        print("📝 QUIZ-POST:")
        print("=" * 50)
        print(post_text)
        print("-" * 50)
        print("Antwortmöglichkeiten:")
        for i, opt in enumerate(quiz.options):
            marker = "✓" if i == quiz.correct_index else " "
            print(f"  [{marker}] {opt}")
        print("=" * 50)
        print(f"📏 Länge: {len(post_text)}/500 Zeichen")

        print("\n" + "=" * 50)
        print("📝 AUFLÖSUNG (wird am nächsten Tag gepostet):")
        print("=" * 50)
        print(solution_text)
        print("=" * 50)
        print(f"📏 Länge: {len(solution_text)}/500 Zeichen\n")

    elif args.test_quiz:
        if not bot.settings.anthropic_api_key:
            print("❌ ANTHROPIC_API_KEY nicht konfiguriert!")
            sys.exit(1)
        if not bot.mastodon.verify_credentials():
            logger.error("invalid_mastodon_credentials")
            sys.exit(1)
        bot._init_quiz_service()
        success = bot.post_quiz()
        if success:
            print("✅ Quiz gepostet")
        else:
            print("❌ Quiz konnte nicht gepostet werden")
        sys.exit(0 if success else 1)
    elif args.quiz_solution:
        if not bot.settings.anthropic_api_key:
            print("❌ ANTHROPIC_API_KEY nicht konfiguriert!")
            sys.exit(1)
        if not bot.mastodon.verify_credentials():
            logger.error("invalid_mastodon_credentials")
            sys.exit(1)
        bot._init_quiz_service()
        success = bot.post_quiz_solution()
        if success:
            print("✅ Quiz-Auflösung gepostet")
        else:
            print("❌ Keine aktive Quiz-Frage oder Fehler beim Posten")
        sys.exit(0 if success else 1)
    elif args.dry_run_repost:
        if not bot.settings.repost_enabled or not bot.settings.repost_accounts:
            print("❌ Repost nicht konfiguriert!")
            print("   Setze REPOST_ENABLED=true und REPOST_ACCOUNTS=Account1,Account2")
            sys.exit(1)
        if not bot.mastodon.verify_credentials():
            logger.error("invalid_mastodon_credentials")
            sys.exit(1)

        from datetime import datetime, timedelta

        accounts = [a.strip() for a in bot.settings.repost_accounts.split(",") if a.strip()]
        cutoff_time = datetime.now().astimezone() - timedelta(hours=24)

        print("\n" + "=" * 50)
        print("🔄 VORSCHAU - Repost/Boost")
        print("=" * 50)
        print(f"Accounts: {', '.join(accounts)}")
        print(f"Zeitfenster: Letzte 24 Stunden (seit {cutoff_time.strftime('%Y-%m-%d %H:%M')})")
        print("=" * 50)

        total_found = 0
        for acct in accounts:
            print(f"\n📌 Account: @{acct}")
            print("-" * 40)

            account = bot.mastodon.search_account(acct)
            if not account:
                print("   ❌ Account nicht gefunden!")
                continue

            print(f"   Name: {account.get('display_name', 'Unbekannt')}")
            print(f"   Follower: {account.get('followers_count', 0)}")

            statuses = bot.mastodon.get_account_statuses(
                account["id"],
                limit=40,
                exclude_replies=True,
                exclude_reblogs=True,
            )

            recent_statuses = []
            for status in statuses:
                created_at = status.get("created_at")
                if not created_at:
                    continue
                if isinstance(created_at, str):
                    try:
                        created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    except ValueError:
                        continue
                if created_at >= cutoff_time:
                    recent_statuses.append((status, created_at))

            if not recent_statuses:
                print("   Keine neuen Beiträge in den letzten 24h")
                continue

            print(f"   Gefundene Beiträge: {len(recent_statuses)}")
            for status, created_at in recent_statuses:
                already_boosted = "✓ bereits" if status.get("reblogged") else "○ neu"
                content = status.get("content", "")[:80].replace("\n", " ")
                # HTML-Tags entfernen für Vorschau
                import re
                content = re.sub(r"<[^>]+>", "", content)
                print(f"\n   [{already_boosted}] {created_at.strftime('%H:%M')}")
                print(f"   {content}...")
                total_found += 1

        print("\n" + "=" * 50)
        print(f"Gesamt: {total_found} Beiträge würden geprüft")
        print("=" * 50 + "\n")

    elif args.repost:
        if not bot.settings.repost_enabled or not bot.settings.repost_accounts:
            print("❌ Repost nicht konfiguriert!")
            print("   Setze REPOST_ENABLED=true und REPOST_ACCOUNTS=Account1,Account2")
            sys.exit(1)
        if not bot.mastodon.verify_credentials():
            logger.error("invalid_mastodon_credentials")
            sys.exit(1)

        accounts = [a.strip() for a in bot.settings.repost_accounts.split(",") if a.strip()]
        print(f"\n🔄 Starte Repost für: {', '.join(accounts)}")

        bot._init_repost_service()
        count = bot.run_repost()

        if count > 0:
            print(f"✅ {count} Beiträge geboosted")
        else:
            print("ℹ️  Keine neuen Beiträge zum Boosten gefunden")
        sys.exit(0)
    elif args.dry_run:
        bot.dry_run()
    elif args.once:
        bot.run_once()
    else:
        bot.run_scheduled()


if __name__ == "__main__":
    main()
