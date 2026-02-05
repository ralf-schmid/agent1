"""Generator für BibleServer URLs."""

import re
from urllib.parse import quote


class BibleLinkGenerator:
    """Generiert Links zu BibleServer für Bibelstellen."""

    # Mapping von deutschen Buchnamen zu BibleServer-Formaten
    BOOK_MAPPINGS = {
        # Altes Testament
        "1. mose": "1.Mose",
        "2. mose": "2.Mose",
        "3. mose": "3.Mose",
        "4. mose": "4.Mose",
        "5. mose": "5.Mose",
        "1 mose": "1.Mose",
        "2 mose": "2.Mose",
        "3 mose": "3.Mose",
        "4 mose": "4.Mose",
        "5 mose": "5.Mose",
        "genesis": "1.Mose",
        "exodus": "2.Mose",
        "levitikus": "3.Mose",
        "numeri": "4.Mose",
        "deuteronomium": "5.Mose",
        "josua": "Josua",
        "richter": "Richter",
        "rut": "Rut",
        "ruth": "Rut",
        "1. samuel": "1.Samuel",
        "2. samuel": "2.Samuel",
        "1 samuel": "1.Samuel",
        "2 samuel": "2.Samuel",
        "1. könige": "1.Könige",
        "2. könige": "2.Könige",
        "1 könige": "1.Könige",
        "2 könige": "2.Könige",
        "1. chronik": "1.Chronik",
        "2. chronik": "2.Chronik",
        "1 chronik": "1.Chronik",
        "2 chronik": "2.Chronik",
        "esra": "Esra",
        "nehemia": "Nehemia",
        "ester": "Ester",
        "esther": "Ester",
        "hiob": "Hiob",
        "psalm": "Psalm",
        "psalmen": "Psalm",
        "sprüche": "Sprüche",
        "prediger": "Prediger",
        "kohelet": "Prediger",
        "hohelied": "Hohelied",
        "jesaja": "Jesaja",
        "jeremia": "Jeremia",
        "klagelieder": "Klagelieder",
        "hesekiel": "Hesekiel",
        "ezechiel": "Hesekiel",
        "daniel": "Daniel",
        "hosea": "Hosea",
        "joel": "Joel",
        "amos": "Amos",
        "obadja": "Obadja",
        "jona": "Jona",
        "micha": "Micha",
        "nahum": "Nahum",
        "habakuk": "Habakuk",
        "zefanja": "Zefanja",
        "haggai": "Haggai",
        "sacharja": "Sacharja",
        "maleachi": "Maleachi",
        # Neues Testament
        "matthäus": "Matthäus",
        "markus": "Markus",
        "lukas": "Lukas",
        "johannes": "Johannes",
        "apostelgeschichte": "Apostelgeschichte",
        "römer": "Römer",
        "1. korinther": "1.Korinther",
        "2. korinther": "2.Korinther",
        "1 korinther": "1.Korinther",
        "2 korinther": "2.Korinther",
        "galater": "Galater",
        "epheser": "Epheser",
        "philipper": "Philipper",
        "kolosser": "Kolosser",
        "1. thessalonicher": "1.Thessalonicher",
        "2. thessalonicher": "2.Thessalonicher",
        "1 thessalonicher": "1.Thessalonicher",
        "2 thessalonicher": "2.Thessalonicher",
        "1. timotheus": "1.Timotheus",
        "2. timotheus": "2.Timotheus",
        "1 timotheus": "1.Timotheus",
        "2 timotheus": "2.Timotheus",
        "titus": "Titus",
        "philemon": "Philemon",
        "hebräer": "Hebräer",
        "jakobus": "Jakobus",
        "1. petrus": "1.Petrus",
        "2. petrus": "2.Petrus",
        "1 petrus": "1.Petrus",
        "2 petrus": "2.Petrus",
        "1. johannes": "1.Johannes",
        "2. johannes": "2.Johannes",
        "3. johannes": "3.Johannes",
        "1 johannes": "1.Johannes",
        "2 johannes": "2.Johannes",
        "3 johannes": "3.Johannes",
        "judas": "Judas",
        "offenbarung": "Offenbarung",
    }

    def __init__(self, base_url: str = "https://www.bibleserver.com", translation: str = "ELB"):
        self.base_url = base_url.rstrip("/")
        self.translation = translation

    def generate_url(self, verse_reference: str) -> str:
        """
        Generiert eine BibleServer URL für eine Bibelstelle.

        Args:
            verse_reference: z.B. "Psalm 145,18" oder "1. Mose 1,1"

        Returns:
            Vollständige URL zu BibleServer
        """
        normalized = self._normalize_reference(verse_reference)
        return f"{self.base_url}/{self.translation}/{quote(normalized, safe=',.')}"

    def generate_short_url(self, verse_reference: str) -> str:
        """Generiert eine verkürzte URL ohne https:// Prefix."""
        normalized = self._normalize_reference(verse_reference)
        base = self.base_url.replace("https://", "").replace("http://", "")
        return f"{base}/{self.translation}/{normalized}"

    def _normalize_reference(self, reference: str) -> str:
        """
        Normalisiert eine Bibelstellenangabe für BibleServer.

        Args:
            reference: z.B. "Psalm 145,18" oder "1. Mose 1, 1-3"

        Returns:
            Normalisierte Referenz z.B. "Psalm145,18"
        """
        # Leerzeichen um Komma entfernen
        reference = re.sub(r"\s*,\s*", ",", reference)
        # Leerzeichen um Bindestrich entfernen
        reference = re.sub(r"\s*-\s*", "-", reference)

        # Buch und Kapitel/Vers trennen
        # Pattern: Buchname (optional mit Zahl davor) + Kapitel,Vers
        match = re.match(r"^(.+?)\s+(\d+.*)$", reference.strip())

        if match:
            book = match.group(1).strip()
            chapter_verse = match.group(2).strip()

            # Buch normalisieren
            book_lower = book.lower()
            if book_lower in self.BOOK_MAPPINGS:
                book = self.BOOK_MAPPINGS[book_lower]

            # Leerzeichen zwischen Buch und Kapitel entfernen
            return f"{book}{chapter_verse}"

        # Fallback: Leerzeichen entfernen
        return reference.replace(" ", "")
