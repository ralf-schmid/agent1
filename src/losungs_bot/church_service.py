"""Gottesdienst-Erinnerungen für den Losungs-Bot."""

from dataclasses import dataclass

import structlog

logger = structlog.get_logger()


@dataclass
class ChurchService:
    """Informationen über einen Gottesdienst."""

    name: str
    times: list[str]
    location: str
    website: str
    online_url: str | None = None


# Konfigurierte Gemeinden
CHURCHES = {
    "icf_karlsruhe": ChurchService(
        name="ICF Karlsruhe",
        times=["10:00 Uhr", "12:00 Uhr"],
        location="Karlsruhe",
        website="https://www.icf-karlsruhe.de/gottesdienst-2/",
        online_url="https://www.icf-karlsruhe.de/online/",
    ),
}


class ChurchServiceReminder:
    """Erstellt Gottesdienst-Erinnerungen."""

    def __init__(self, church_id: str = "icf_karlsruhe"):
        """
        Initialisiert den Reminder für eine Gemeinde.

        Args:
            church_id: ID der Gemeinde (z.B. "icf_karlsruhe")
        """
        if church_id not in CHURCHES:
            raise ValueError(f"Unbekannte Gemeinde: {church_id}")

        self.church = CHURCHES[church_id]
        logger.info("church_reminder_initialized", church=self.church.name)

    def format_saturday_reminder(self) -> str:
        """
        Formatiert die Samstags-Erinnerung für den Sonntagsgottesdienst.

        Returns:
            Formatierter Post-Text
        """
        times_str = " und ".join(self.church.times)

        post = f"""⛪ Gottesdienst-Erinnerung

Morgen ist Sonntag – eine gute Gelegenheit, einen Gottesdienst zu besuchen! 🙏

📍 {self.church.name}
🕐 {times_str}
🔗 {self.church.website}"""

        if self.church.online_url:
            post += f"""

💻 Auch online verfügbar:
🔗 {self.church.online_url}"""

        post += """

Wo auch immer du hingehst – vor Ort oder online – möge Gott dich segnen! ✨

#Gottesdienst #Sonntag #Kirche"""

        return post
