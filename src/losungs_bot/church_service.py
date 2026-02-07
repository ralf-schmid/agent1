"""Gottesdienst-Erinnerungen für den Losungs-Bot."""

import structlog

logger = structlog.get_logger()

# ICF Karlsruhe Website
ICF_KARLSRUHE_URL = "https://www.icf-karlsruhe.de/gottesdienst-2/"


class ChurchServiceReminder:
    """Erstellt Gottesdienst-Erinnerungen."""

    def __init__(self):
        """Initialisiert den Reminder."""
        logger.info("church_reminder_initialized")

    def format_saturday_reminder(self) -> str:
        """
        Formatiert die Samstags-Erinnerung für den Sonntagsgottesdienst.

        Returns:
            Formatierter Post-Text
        """
        return f"""⛪ Gottesdienst-Erinnerung

Morgen ist Sonntag – eine gute Gelegenheit, einen Gottesdienst zu besuchen! 🙏

📍 bei Dir vor Ort
💻 oder online

Wenn Du in der Nähe von Karlsruhe bist, schau gerne im ICF Karlsruhe vorbei: 🔗 {ICF_KARLSRUHE_URL}

#Gottesdienst #Sonntag #Kirche #icf #icf-karlsruhe #Karlsruhe"""
