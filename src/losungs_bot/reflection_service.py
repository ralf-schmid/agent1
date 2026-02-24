"""Service für tägliche Reflexionsfragen zur Losung."""

import structlog

from losungs_bot.ai_client import AIClient
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

    def __init__(self, ai_client: AIClient | None = None, api_key: str | None = None):
        """
        Initialisiert den Reflexions-Service.

        Args:
            ai_client: Gemeinsamer AI-Client (bevorzugt)
            api_key: Anthropic API Key (falls kein Client übergeben)
        """
        if ai_client:
            self.ai_client = ai_client
        elif api_key:
            self.ai_client = AIClient(api_key)
        else:
            raise ValueError("Either ai_client or api_key must be provided")
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

        question = self.ai_client.generate(
            user_prompt=user_prompt,
            system_prompt=self.SYSTEM_PROMPT,
            max_tokens=200,
        )

        if not question:
            return None

        # Anführungszeichen am Anfang und Ende entfernen
        question = question.lstrip('"\'').rstrip('"\'')

        logger.info(
            "reflection_generated",
            question_preview=question[:50],
        )

        return question

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

#Losung #FediKirche #Reflexion #Glaube"""
