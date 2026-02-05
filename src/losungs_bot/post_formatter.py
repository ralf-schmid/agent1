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

    # Copyright-Hinweis gemäß Nutzungsbedingungen losungen.de
    COPYRIGHT = "© Evangelische Brüder-Unität – Herrnhuter Brüdergemeine"
    COPYRIGHT_URL = "https://www.herrnhuter.de"
    INFO_URL = "https://www.losungen.de"

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

        post = f"""📖 Die Losungen – {datum_str}

✨ „{losung.losungstext}"
— {losung.losungsvers}
🔗 {losung_url}

💫 „{losung.lehrtext}"
— {losung.lehrtextvers}
🔗 {lehrtext_url}

{self.COPYRIGHT}
🔗 {self.COPYRIGHT_URL}
ℹ️ {self.INFO_URL}

#DieLosungen #Bibel #Herrnhut"""

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
