"""Formatierung der Losungs-Posts für Mastodon."""

from datetime import date

from losungs_bot.bible_links import BibleLinkGenerator
from losungs_bot.losungen import Losung


class PostFormatter:
    """Formatiert Losungen als Mastodon-Posts mit Emojis."""

    # Deutsche Monatsnamen
    MONTHS = [
        "",
        "Januar",
        "Februar",
        "März",
        "April",
        "Mai",
        "Juni",
        "Juli",
        "August",
        "September",
        "Oktober",
        "November",
        "Dezember",
    ]

    # Grüße je nach Tageszeit (für zukünftige Erweiterung)
    GREETINGS = [
        "Guten Morgen! ☀️",
        "Einen wunderschönen guten Morgen! 🌅",
        "Hallo und guten Morgen! 🌤️",
        "Guten Morgen, ihr Lieben! 💫",
    ]

    # Abschlussgrüße
    CLOSINGS = [
        "Einen gesegneten Tag euch allen! 🙏",
        "Habt einen wundervollen Tag! ✨",
        "Seid gesegnet heute! 🙏💕",
        "Gottes Segen für den Tag! 🙏",
    ]

    def __init__(self, bible_link_generator: BibleLinkGenerator):
        self.bible_links = bible_link_generator

    def format_post(self, losung: Losung) -> str:
        """
        Formatiert eine Losung als Mastodon-Post.

        Args:
            losung: Die zu formatierende Losung

        Returns:
            Formatierter Post-Text (max. 500 Zeichen für Mastodon)
        """
        datum_str = self._format_date(losung.datum)

        # URLs generieren
        losung_url = self.bible_links.generate_short_url(losung.losungsvers)
        lehrtext_url = self.bible_links.generate_short_url(losung.lehrtextvers)

        # Greeting basierend auf Tag des Jahres für Abwechslung
        greeting_idx = losung.datum.timetuple().tm_yday % len(self.GREETINGS)
        closing_idx = losung.datum.timetuple().tm_yday % len(self.CLOSINGS)

        post = f"""{self.GREETINGS[greeting_idx]} Hier kommt die Losung für den {datum_str} 📖

✨ Losung (AT):
„{losung.losungstext}"
— {losung.losungsvers}
🔗 {losung_url}

💫 Lehrtext (NT):
„{losung.lehrtext}"
— {losung.lehrtextvers}
🔗 {lehrtext_url}

{self.CLOSINGS[closing_idx]}

#Losung #Bibel #Herrnhut #Glaube #Elberfelder"""

        return post

    def _format_date(self, datum: date) -> str:
        """Formatiert ein Datum auf Deutsch."""
        return f"{datum.day}. {self.MONTHS[datum.month]} {datum.year}"

    def validate_length(self, post: str, max_length: int = 500) -> bool:
        """Prüft, ob der Post die maximale Länge nicht überschreitet."""
        return len(post) <= max_length

    def get_post_length(self, post: str) -> int:
        """Gibt die Länge des Posts zurück."""
        return len(post)
