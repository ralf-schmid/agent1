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

    # Losungen
    losungen_file: str = Field(default="data/losungen.xml")


def get_settings() -> Settings:
    """Erstellt und gibt die Einstellungen zurück."""
    return Settings()
