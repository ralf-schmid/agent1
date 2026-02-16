"""Formatierung der Losungs-Posts für Mastodon."""

from dataclasses import dataclass
from datetime import date

from losungs_bot.bible_links import BibleLinkGenerator
from losungs_bot.losungen import Losung


@dataclass
class FormattedPost:
    """Ein formatierter Post, möglicherweise mit Copyright-Antwort."""

    main_post: str
    copyright_reply: str | None = None

    @property
    def needs_reply(self) -> bool:
        """True wenn der Copyright-Text als separate Antwort gepostet werden muss."""
        return self.copyright_reply is not None


class PostFormatter:
    """Formatiert Losungen als Mastodon-Posts mit Emojis."""

    MAX_LENGTH = 500

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

    # Standard Podcast-Links
    DEFAULT_PODCAST_APPLE = (
        "https://podcasts.apple.com/de/podcast/die-losungen/id1434728607"
    )
    DEFAULT_PODCAST_SPOTIFY = "https://open.spotify.com/show/12L3SnnMI5JMDJVtQCqBxh"

    def __init__(
        self,
        bible_link_generator: BibleLinkGenerator,
        podcast_apple: str | None = None,
        podcast_spotify: str | None = None,
    ):
        self.bible_links = bible_link_generator
        self.podcast_apple = podcast_apple or self.DEFAULT_PODCAST_APPLE
        self.podcast_spotify = podcast_spotify or self.DEFAULT_PODCAST_SPOTIFY

    def format_post(self, losung: Losung) -> FormattedPost:
        """
        Formatiert eine Losung als Mastodon-Post.

        Wenn der vollständige Post zu lang ist, wird er automatisch aufgeteilt:
        - Hauptpost: Bibelverse mit Links und Hashtags
        - Antwort: Copyright-Hinweise

        Args:
            losung: Die zu formatierende Losung

        Returns:
            FormattedPost mit main_post und optional copyright_reply
        """
        # Versuche zuerst den kompakten Einzel-Post
        single_post = self._format_single_post(losung)
        if len(single_post) <= self.MAX_LENGTH:
            return FormattedPost(main_post=single_post)

        # Wenn zu lang: aufteilen in Hauptpost und Copyright-Antwort
        main_post = self._format_main_post(losung)
        copyright_reply = self._format_copyright_reply()

        return FormattedPost(main_post=main_post, copyright_reply=copyright_reply)

    def _format_single_post(self, losung: Losung) -> str:
        """Formatiert einen kompakten Einzel-Post (wenn möglich)."""
        datum_str = self._format_date(losung.datum)
        losung_url = self.bible_links.generate_url(losung.losungsvers)
        lehrtext_url = self.bible_links.generate_url(losung.lehrtextvers)

        return f"""📖 Die Losungen – {datum_str}

✨ „{losung.losungstext}"
— {losung.losungsvers}
🔗 {losung_url}

💫 „{losung.lehrtext}"
— {losung.lehrtextvers}
🔗 {lehrtext_url}

{self.COPYRIGHT}
🔗 {self.COPYRIGHT_URL}
ℹ️ {self.INFO_URL}

#losung #DieLosungen #Bibel #Herrnhut #Jesus #Bibelvers #Gotteswort #Glaube #Gott #fediKirche #Motivation #Inspiration"""

    def _format_main_post(self, losung: Losung) -> str:
        """Formatiert den Hauptpost mit Bibelversen (ohne Copyright, ohne Hashtags)."""
        datum_str = self._format_date(losung.datum)
        losung_url = self.bible_links.generate_url(losung.losungsvers)
        lehrtext_url = self.bible_links.generate_url(losung.lehrtextvers)

        return f"""📖 Die Losungen – {datum_str}

✨ „{losung.losungstext}"
— {losung.losungsvers}
🔗 {losung_url}

💫 „{losung.lehrtext}"
— {losung.lehrtextvers}
🔗 {lehrtext_url}"""

    def _format_copyright_reply(self) -> str:
        """Formatiert die Copyright-Antwort mit Podcast-Links und Hashtags."""
        return f"""{self.COPYRIGHT}
🔗 {self.COPYRIGHT_URL}
ℹ️ {self.INFO_URL}

🎧 Als Podcast:
🍎 {self.podcast_apple}
🟢 {self.podcast_spotify}

#losung #DieLosungen #Bibel #Herrnhut #Jesus #Bibelvers #Gotteswort #Glaube #Gott #Motivation #Inspiration"""

    def _format_date(self, datum: date) -> str:
        """Formatiert ein Datum auf Deutsch."""
        return f"{datum.day}. {self.MONTHS[datum.month]} {datum.year}"

    def validate_length(self, post: str, max_length: int = 500) -> bool:
        """Prüft, ob der Post die maximale Länge nicht überschreitet."""
        return len(post) <= max_length

    def get_post_length(self, post: str) -> int:
        """Gibt die Länge des Posts zurück."""
        return len(post)
