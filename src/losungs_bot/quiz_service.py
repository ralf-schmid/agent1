"""Bibelquiz-Service mit KI-generierter Fragestellung."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import structlog

from losungs_bot.ai_client import AIClient
from losungs_bot.losungen import Losung

logger = structlog.get_logger()


@dataclass
class QuizQuestion:
    """Eine Quiz-Frage mit Antwortmöglichkeiten."""

    question: str
    options: list[str]  # 4 Optionen
    correct_index: int  # 0-3
    explanation: str
    losung_reference: str  # z.B. "Jesaja 41,10"


class QuizService:
    """Service für KI-generierte Bibelquiz-Fragen."""

    SYSTEM_PROMPT = """Du bist ein Experte für die Bibel und erstellst Quiz-Fragen.
Deine Aufgabe ist es, eine interessante und lehrreiche Quiz-Frage zu einer Bibelstelle zu erstellen.

WICHTIG: Die Bibelstelle (Buch, Kapitel, Vers) wird den Teilnehmern NICHT gezeigt!
Du kannst also auch nach dem Buch oder dem Verfasser fragen.

Regeln:
1. Die Frage muss faktisch korrekt und verifizierbar sein
2. Erstelle genau 4 Antwortmöglichkeiten
3. Nur EINE Antwort darf richtig sein
4. Die falschen Antworten müssen plausibel klingen
5. Die Frage soll zum Nachdenken anregen und lehrreich sein
6. Mögliche Fragetypen:
   - Aus welchem Buch der Bibel stammt dieser Vers?
   - Wer hat dieses Buch geschrieben/verfasst?
   - Historischer Kontext (Jahrhundert, Ort, Situation)
   - Wer sprach diese Worte ursprünglich?
   - Was bedeutet ein bestimmtes Wort/Begriff im Text?
   - An wen waren diese Worte gerichtet?

Antworte NUR mit validem JSON im folgenden Format:
{
  "question": "Die Quizfrage",
  "options": ["Option A", "Option B", "Option C", "Option D"],
  "correct_index": 0,
  "explanation": "Kurze Erklärung warum die Antwort richtig ist (1-2 Sätze)"
}"""

    def __init__(self, ai_client: AIClient | None = None, api_key: str | None = None):
        """
        Initialisiert den Quiz-Service.

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
        logger.info("quiz_service_initialized")

    def generate_quiz(self, losung: Losung) -> QuizQuestion | None:
        """
        Generiert eine Quiz-Frage basierend auf der Tageslosung.

        Args:
            losung: Die Tageslosung als Basis für die Frage

        Returns:
            QuizQuestion oder None bei Fehler
        """
        user_prompt = f"""Erstelle eine Quiz-Frage zur folgenden Bibelstelle:

Bibelstelle (wird den Teilnehmern NICHT gezeigt): {losung.losungsvers}
Text (wird den Teilnehmern gezeigt): "{losung.losungstext}"

Die Frage kann nach dem Buch, Verfasser, historischen Kontext oder der Bedeutung fragen."""

        try:
            content = self.ai_client.generate(
                user_prompt=user_prompt,
                system_prompt=self.SYSTEM_PROMPT,
                max_tokens=500,
            )

            if not content:
                return None

            # JSON aus der Antwort extrahieren
            quiz_data = json.loads(content)

            quiz = QuizQuestion(
                question=quiz_data["question"],
                options=quiz_data["options"],
                correct_index=quiz_data["correct_index"],
                explanation=quiz_data["explanation"],
                losung_reference=losung.losungsvers,
            )

            logger.info(
                "quiz_generated",
                reference=quiz.losung_reference,
                question_preview=quiz.question[:50],
            )

            return quiz

        except json.JSONDecodeError as e:
            logger.error("quiz_json_parse_error", error=str(e), response=content)
            return None
        except Exception as e:
            logger.error("quiz_generation_failed", error=str(e))
            return None

    def format_quiz_post(self, quiz: QuizQuestion, losung_text: str) -> str:
        """
        Formatiert die Quiz-Frage für einen Mastodon-Post.

        Args:
            quiz: Die Quiz-Frage
            losung_text: Der Losungstext (ohne Quellenangabe)

        Returns:
            Formatierter Post-Text (ohne Poll-Optionen)
        """
        return f"""📖 Bibelquiz

„{losung_text}"

{quiz.question}

#Bibelquiz #Bibel"""

    def format_solution_post(
        self, quiz: QuizQuestion, poll_results: dict | None = None
    ) -> str:
        """
        Formatiert die Auflösung für einen Mastodon-Post.

        Args:
            quiz: Die Quiz-Frage
            poll_results: Optionale Poll-Ergebnisse

        Returns:
            Formatierter Auflösungs-Post
        """
        correct_answer = quiz.options[quiz.correct_index]

        text = f"""📖 Quiz-Auflösung

✅ Richtige Antwort: {correct_answer}

{quiz.explanation}

(Bibelstelle: {quiz.losung_reference})"""

        # Poll-Ergebnisse hinzufügen wenn verfügbar
        if poll_results and poll_results.get("votes_count", 0) > 0:
            total_votes = poll_results["votes_count"]
            correct_votes = poll_results["options"][quiz.correct_index].get(
                "votes_count", 0
            )
            percentage = (
                round(correct_votes / total_votes * 100) if total_votes > 0 else 0
            )

            if percentage >= 70:
                emoji = "🎉"
            elif percentage >= 50:
                emoji = "👍"
            else:
                emoji = "📚"

            text += f"\n\n{percentage}% haben richtig geantwortet! {emoji}"

        return text


class QuizStateManager:
    """Verwaltet den Zustand aktiver Quizze."""

    def __init__(self, state_file: str):
        """
        Initialisiert den State Manager.

        Args:
            state_file: Pfad zur State-Datei
        """
        self.state_file = Path(state_file)
        self._state: dict = {}
        self._load_state()

    def _load_state(self) -> None:
        """Lädt den State aus der Datei."""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    self._state = json.load(f)
                logger.info("quiz_state_loaded", active_quiz=self.has_active_quiz())
            except Exception as e:
                logger.error("quiz_state_load_failed", error=str(e))
                self._state = {}
        else:
            self._state = {}

    def _save_state(self) -> None:
        """Speichert den State in die Datei."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, "w") as f:
                json.dump(self._state, f, indent=2)
            logger.info("quiz_state_saved")
        except Exception as e:
            logger.error("quiz_state_save_failed", error=str(e))

    def save_active_quiz(
        self,
        quiz: QuizQuestion,
        status_id: str,
        poll_id: str,
    ) -> None:
        """
        Speichert ein aktives Quiz.

        Args:
            quiz: Die Quiz-Frage
            status_id: Mastodon Status-ID
            poll_id: Mastodon Poll-ID
        """
        self._state = {
            "quiz": asdict(quiz),
            "status_id": status_id,
            "poll_id": poll_id,
        }
        self._save_state()
        logger.info(
            "active_quiz_saved",
            status_id=status_id,
            poll_id=poll_id,
        )

    def get_active_quiz(self) -> tuple[QuizQuestion, str, str] | None:
        """
        Gibt das aktive Quiz zurück.

        Returns:
            Tuple (QuizQuestion, status_id, poll_id) oder None
        """
        if not self._state or "quiz" not in self._state:
            return None

        quiz_data = self._state["quiz"]
        quiz = QuizQuestion(
            question=quiz_data["question"],
            options=quiz_data["options"],
            correct_index=quiz_data["correct_index"],
            explanation=quiz_data["explanation"],
            losung_reference=quiz_data["losung_reference"],
        )
        return quiz, self._state["status_id"], self._state["poll_id"]

    def has_active_quiz(self) -> bool:
        """Prüft ob ein aktives Quiz existiert."""
        return bool(self._state and "quiz" in self._state)

    def clear_active_quiz(self) -> None:
        """Löscht das aktive Quiz."""
        self._state = {}
        self._save_state()
        logger.info("active_quiz_cleared")
