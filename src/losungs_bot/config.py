"""Konfiguration für den Losungs-Bot."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Anwendungskonfiguration aus Umgebungsvariablen."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Mastodon
    mastodon_instance: str = Field(default="https://mastodon.social")
    mastodon_access_token: str = Field(...)

    # Scheduling
    post_time: str = Field(default="06:00")
    timezone: str = Field(default="Europe/Berlin")

    # Bibel
    bible_translation: str = Field(default="ELB")
    bible_server_base_url: str = Field(default="https://www.bibleserver.com")

    # Losungen - kann Datei oder Verzeichnis sein
    # Bei Verzeichnis werden alle "Losungen*.xml" Dateien geladen
    losungen_file: str = Field(default="data/")

    # Gottesdienst-Erinnerung (Samstag)
    church_reminder_enabled: bool = Field(default=True)
    church_reminder_time: str = Field(default="17:00")
    church_reminder_day: int = Field(default=5)  # 0=Mo, 5=Sa, 6=So

    # Follower-Interaktionen
    auto_follow_back: bool = Field(default=True)
    welcome_message_enabled: bool = Field(default=True)
    follower_check_time: str = Field(default="08:00")  # Täglich um 08:00
    follower_state_file: str = Field(default="data/follower_state.json")

    # Admin-Benachrichtigungen
    admin_notify_account: str | None = Field(default=None)

    # Podcast-Links
    podcast_apple: str = Field(
        default="https://podcasts.apple.com/de/podcast/die-losungen/id1434728607"
    )
    podcast_spotify: str = Field(
        default="https://open.spotify.com/show/12L3SnnMI5JMDJVtQCqBxh"
    )


def get_settings() -> Settings:
    """Erstellt und gibt die Einstellungen zurück."""
    return Settings()
