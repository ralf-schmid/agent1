"""Service für tägliche Reflexionsfragen zur Losung."""

import structlog
from anthropic import Anthropic

from losungs_bot.losungen import Losung

logger = structlog.get_logger()


class ReflectionService:
    """Generiert Reflexionsfragen zur täglichen Losung."""

    SYSTEM_PROMPT = """Du bist ein einfühlsamer Seelsorger und erstellst Reflexionsfragen.
Deine Aufgabe ist es, eine nachdenkliche Frage zu einem Bibelvers zu formulieren.

Regeln:
1. Die Frage soll zum persönlichen Nachdenken anregen
2. Sie soll alltagsnah und praktisch sein
3. Nicht zu theologisch oder kompliziert
4. Offen formuliert (keine Ja/Nein-Fragen)
5. Maximal 1-2 Sätze
6. Respektvoll und einladend

Antworte NUR mit der Reflexionsfrage, ohne Anführungszeichen oder Zusätze."""

    def __init__(self, api_key: str):
        """
        Initialisiert den Reflexions-Service.

        Args:
            api_key: Anthropic API Key
        """
        self.client = Anthropic(api_key=api_key)
        logger.info("reflection_service_initialized")

    def generate_reflection(self, losung: Losung) -> str | None:
        """
        Generiert eine Reflexionsfrage zur Losung.

        Args:
            losung: Die Tageslosung

        Returns:
            Die Reflexionsfrage oder None bei Fehler
        """
        user_prompt = f"""Erstelle eine Reflexionsfrage zu diesem Bibelvers:

"{losung.losungstext}"
— {losung.losungsvers}

Die Frage soll Menschen helfen, den Vers auf ihr eigenes Leben anzuwenden."""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=200,
                messages=[{"role": "user", "content": user_prompt}],
                system=self.SYSTEM_PROMPT,
            )

            question = response.content[0].text.strip()

            # Anführungszeichen am Anfang und Ende entfernen
            question = question.lstrip('"\'').rstrip('"\'')

            logger.info(
                "reflection_generated",
                question_preview=question[:50],
            )

            return question

        except Exception as e:
            logger.error("reflection_generation_failed", error=str(e))
            return None

    def format_reflection_post(self, losung: Losung, question: str) -> str:
        """
        Formatiert den Reflexions-Post.

        Args:
            losung: Die Tageslosung
            question: Die generierte Reflexionsfrage

        Returns:
            Formatierter Post-Text
        """
        return f"""💭 Mittagsimpuls

„{losung.losungstext}"
— {losung.losungsvers}

🤔 {question}

#Losung #Reflexion #Glaube"""
