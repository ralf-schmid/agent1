"""Gemeinsamer AI-Client für Quiz und Reflexion."""

import structlog
from anthropic import Anthropic

logger = structlog.get_logger()


class AIClient:
    """Wrapper für den Anthropic-Client."""

    DEFAULT_MODEL = "claude-3-haiku-20240307"

    def __init__(self, api_key: str):
        """
        Initialisiert den AI-Client.

        Args:
            api_key: Anthropic API Key
        """
        self._client = Anthropic(api_key=api_key)
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
            return None
