"""Gemeinsamer AI-Client für Quiz und Reflexion."""

import time
from collections.abc import Callable

import structlog
from anthropic import Anthropic

logger = structlog.get_logger()


class AIClient:
    """Wrapper für den Anthropic-Client."""

    DEFAULT_MODEL = "claude-haiku-4-5"

    # Fehler-Benachrichtigung höchstens alle 6 Stunden, damit z.B. die
    # Erwähnungsprüfung (alle 5 Minuten) keine DM-Flut auslöst
    ERROR_NOTIFY_COOLDOWN = 6 * 3600

    def __init__(
        self,
        api_key: str,
        on_error: Callable[[str], None] | None = None,
    ):
        """
        Initialisiert den AI-Client.

        Args:
            api_key: Anthropic API Key
            on_error: Optionaler Callback bei fehlgeschlagenem KI-Aufruf
                (erhält die Fehlermeldung, gedrosselt)
        """
        self._client = Anthropic(api_key=api_key)
        self._on_error = on_error
        self._last_error_notify: float | None = None
        logger.info("ai_client_initialized")

    def generate(
        self,
        user_prompt: str,
        system_prompt: str,
        max_tokens: int = 500,
        model: str | None = None,
    ) -> str | None:
        """
        Generiert eine Antwort vom AI-Modell.

        Args:
            user_prompt: Die Nutzeranfrage
            system_prompt: Der System-Prompt
            max_tokens: Maximale Anzahl Tokens
            model: Optional anderes Modell

        Returns:
            Die generierte Antwort oder None bei Fehler
        """
        try:
            response = self._client.messages.create(
                model=model or self.DEFAULT_MODEL,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": user_prompt}],
                system=system_prompt,
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.error("ai_generation_failed", error=str(e))
            self._notify_error(str(e))
            return None

    def _notify_error(self, error: str) -> None:
        """Ruft den Fehler-Callback auf (höchstens einmal pro Cooldown)."""
        if not self._on_error:
            return
        now = time.monotonic()
        if (
            self._last_error_notify is not None
            and now - self._last_error_notify < self.ERROR_NOTIFY_COOLDOWN
        ):
            return
        self._last_error_notify = now
        try:
            self._on_error(error)
        except Exception as e:
            logger.error("ai_error_notify_failed", error=str(e))
