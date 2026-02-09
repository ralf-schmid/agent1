"""Handler für Erwähnungen und Interaktionen."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import structlog

from losungs_bot.bible_links import BibleLinkGenerator
from losungs_bot.losungen import LosungenParser

if TYPE_CHECKING:
    from losungs_bot.activity_logger import ActivityLogger
    from losungs_bot.metrics import MetricsCollector

logger = structlog.get_logger()


class MentionHandler:
    """Verarbeitet Erwähnungen und reagiert auf Befehle."""

    # Bekannte Befehle - Reihenfolge wichtig! Spezifische zuerst.
    COMMANDS = [
        ("zufall", "verse_random"),
        ("random", "verse_random"),
        ("quiz", "quiz"),
        ("hilfe", "help"),
        ("help", "help"),
        ("?", "help"),
        ("vers", "verse_today"),
        ("losung", "verse_today"),
        ("heute", "verse_today"),
    ]

    # Regex für Bibelstellen (z.B. "Johannes 3,16" oder "1. Mose 1,1")
    VERSE_PATTERN = re.compile(
        r"(\d\.\s*)?([\wäöüÄÖÜß]+)\s+(\d+)[,:](\d+)(?:-(\d+))?",
        re.IGNORECASE,
    )

    def __init__(
        self,
        mastodon_client,
        losungen_parser: LosungenParser,
        bible_links: BibleLinkGenerator,
        quiz_service=None,
        activity_logger: ActivityLogger | None = None,
        metrics_collector: MetricsCollector | None = None,
    ):
        """
        Initialisiert den Mention-Handler.

        Args:
            mastodon_client: Mastodon Client für Antworten
            losungen_parser: Parser für Losungen
            bible_links: Generator für Bibel-Links
            quiz_service: Optional - Quiz-Service für Quiz auf Abruf
            activity_logger: Optional - Logger für Aktivitäten
            metrics_collector: Optional - Collector für Prometheus-Metriken
        """
        self.mastodon = mastodon_client
        self.losungen = losungen_parser
        self.bible_links = bible_links
        self.quiz_service = quiz_service
        self.activity_logger = activity_logger
        self.metrics = metrics_collector
        logger.info("mention_handler_initialized")

    def process_mention(self, notification: dict) -> bool:
        """
        Verarbeitet eine Erwähnung.

        Args:
            notification: Die Notification von Mastodon

        Returns:
            True wenn erfolgreich verarbeitet
        """
        status = notification.get("status", {})
        content = self._strip_html(status.get("content", ""))
        account = notification.get("account", {})
        username = account.get("acct", "unknown")
        status_id = status.get("id")

        logger.info(
            "processing_mention",
            from_user=username,
            content_preview=content[:50],
        )

        # Eigenen Bot-Namen aus dem Text entfernen
        content_clean = self._remove_mentions(content).strip().lower()

        # Befehl erkennen
        command = self._detect_command(content_clean)

        if command == "help":
            success = self._reply_help(status_id, username)
            if success:
                self._log_mention_response(username, "Hilfe gesendet")
                self._record_mention_metric("help")
            return success
        elif command == "verse_today":
            success = self._reply_verse_today(status_id, username)
            if success:
                self._log_mention_response(username, "Tageslosung gesendet")
                self._record_mention_metric("verse_today")
            return success
        elif command == "verse_random":
            success = self._reply_verse_random(status_id, username)
            if success:
                self._log_mention_response(username, "Zufällige Losung gesendet")
                self._record_mention_metric("verse_random")
            return success
        elif command == "quiz":
            success = self._reply_quiz(status_id, username)
            if success:
                self._log_mention_response(username, "Quiz gestartet")
                self._record_mention_metric("quiz")
            return success
        else:
            # Versuche Bibelstelle zu erkennen
            verse_match = self.VERSE_PATTERN.search(content)
            if verse_match:
                success = self._reply_verse_link(status_id, username, verse_match)
                if success:
                    self._log_mention_response(username, "Bibelstellen-Link gesendet")
                    self._record_mention_metric("verse_link")
                return success

            # Fallback: Hilfe anbieten
            success = self._reply_unknown(status_id, username)
            if success:
                self._log_mention_response(username, "Unbekannte Anfrage beantwortet")
                self._record_mention_metric("unknown")
            return success

    def _detect_command(self, content: str) -> str | None:
        """Erkennt einen Befehl im Text. Spezifische Befehle haben Priorität."""
        for keyword, command in self.COMMANDS:
            if keyword in content:
                return command
        return None

    def _strip_html(self, html: str) -> str:
        """Entfernt HTML-Tags aus dem Text."""
        # Einfaches HTML-Stripping
        clean = re.sub(r"<[^>]+>", " ", html)
        clean = re.sub(r"\s+", " ", clean)
        return clean.strip()

    def _remove_mentions(self, text: str) -> str:
        """Entfernt @mentions aus dem Text."""
        return re.sub(r"@[\w_]+(@[\w.]+)?", "", text)

    def _reply_help(self, status_id: str, username: str) -> bool:
        """Antwortet mit Hilfe-Text."""
        reply = f"""@{username} 👋 Hier ist, was ich kann:

📖 "losung" oder "heute" → Tageslosung
🎲 "zufall" → Zufällige Losung
📚 "Johannes 3,16" → Link zur Bibelstelle
❓ "quiz" → Starte ein Quiz

Täglich um 6:00: Tageslosung
Täglich um 12:00: Reflexionsfrage
Mittwochs 18:00: Bibelquiz"""

        return self._send_reply(status_id, reply)

    def _reply_verse_today(self, status_id: str, username: str) -> bool:
        """Antwortet mit der heutigen Losung."""
        losung = self.losungen.get_today()
        if not losung:
            return self._send_reply(
                status_id,
                f"@{username} Leider konnte ich die heutige Losung nicht finden. 😔",
            )

        link = self.bible_links.generate_url(losung.losungsvers)
        reply = f"""@{username} 📖 Die heutige Losung:

„{losung.losungstext}"
— {losung.losungsvers}

🔗 {link}"""

        return self._send_reply(status_id, reply)

    def _reply_verse_random(self, status_id: str, username: str) -> bool:
        """Antwortet mit einer zufälligen Losung."""
        import random
        from datetime import date, timedelta

        # Zufälliges Datum aus dem aktuellen Jahr
        today = date.today()
        start = date(today.year, 1, 1)
        days = (today - start).days
        random_day = start + timedelta(days=random.randint(0, days))

        losung = self.losungen.get_losung(random_day)
        if not losung:
            return self._send_reply(
                status_id,
                f"@{username} Konnte keine zufällige Losung finden. 😔",
            )

        link = self.bible_links.generate_url(losung.losungsvers)
        reply = f"""@{username} 🎲 Zufällige Losung ({losung.datum.strftime('%d.%m.')}):

„{losung.losungstext}"
— {losung.losungsvers}

🔗 {link}"""

        return self._send_reply(status_id, reply)

    def _reply_quiz(self, status_id: str, username: str) -> bool:
        """Startet ein Quiz als Antwort."""
        if not self.quiz_service:
            return self._send_reply(
                status_id,
                f"@{username} Quiz ist leider nicht verfügbar. 😔",
            )

        losung = self.losungen.get_today()
        if not losung:
            return self._send_reply(
                status_id,
                f"@{username} Konnte keine Losung für das Quiz finden. 😔",
            )

        quiz = self.quiz_service.generate_quiz(losung)
        if not quiz:
            return self._send_reply(
                status_id,
                f"@{username} Quiz-Generierung fehlgeschlagen. Bitte später erneut versuchen. 😔",
            )

        post_text = f"""@{username} 📖 Quiz für dich!

„{losung.losungstext}"

{quiz.question}"""

        # Poll als Antwort posten
        try:
            result = self.mastodon._client.status_post(
                status=post_text,
                in_reply_to_id=status_id,
                poll={
                    "options": quiz.options,
                    "expires_in": 3600,  # 1 Stunde für On-Demand Quiz
                },
                visibility="unlisted",  # Nicht im öffentlichen Feed
            )
            logger.info("quiz_reply_posted", status_id=result["id"])
            return True
        except Exception as e:
            logger.error("quiz_reply_failed", error=str(e))
            return False

    def _reply_verse_link(
        self, status_id: str, username: str, match: re.Match
    ) -> bool:
        """Antwortet mit einem Link zur angefragten Bibelstelle."""
        prefix = match.group(1) or ""
        book = match.group(2)
        chapter = match.group(3)
        verse_start = match.group(4)
        verse_end = match.group(5)

        # Referenz zusammenbauen
        reference = f"{prefix}{book} {chapter},{verse_start}"
        if verse_end:
            reference += f"-{verse_end}"

        link = self.bible_links.generate_url(reference)

        reply = f"""@{username} 📖 {reference}

🔗 {link}

(Elberfelder Übersetzung auf BibleServer)"""

        return self._send_reply(status_id, reply)

    def _reply_unknown(self, status_id: str, username: str) -> bool:
        """Antwortet bei unbekanntem Befehl."""
        reply = f"""@{username} Ich habe dich leider nicht verstanden. 🤔

Schreib "hilfe" für eine Liste meiner Befehle!"""

        return self._send_reply(status_id, reply)

    def _send_reply(self, status_id: str, content: str) -> bool:
        """Sendet eine Antwort."""
        try:
            result = self.mastodon._client.status_post(
                status=content,
                in_reply_to_id=status_id,
                visibility="unlisted",
            )
            logger.info("mention_reply_sent", status_id=result["id"])
            return True
        except Exception as e:
            logger.error("mention_reply_failed", error=str(e))
            return False

    def _log_mention_response(self, username: str, reaction: str) -> None:
        """Loggt eine Mention-Reaktion falls ein Logger vorhanden ist."""
        if self.activity_logger:
            self.activity_logger.log_mention_response(username, reaction)

    def _record_mention_metric(self, command: str) -> None:
        """Zeichnet eine Mention-Metrik auf falls ein Collector vorhanden ist."""
        if self.metrics:
            self.metrics.record_mention(command)
