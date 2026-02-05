"""Parser für die Herrnhuter Losungen XML-Datei."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import structlog

logger = structlog.get_logger()


@dataclass
class Losung:
    """Eine einzelne Tageslosung mit Lehrtext."""

    datum: date
    losungstext: str
    losungsvers: str
    lehrtext: str
    lehrtextvers: str


class LosungenParser:
    """Parser für die jährliche Losungen XML-Datei."""

    def __init__(self, xml_path: str | Path):
        self.xml_path = Path(xml_path)
        self._losungen: dict[date, Losung] = {}
        self._load()

    def _load(self) -> None:
        """Lädt und parst die XML-Datei."""
        if not self.xml_path.exists():
            logger.warning("losungen_file_not_found", path=str(self.xml_path))
            return

        try:
            tree = ET.parse(self.xml_path)
            root = tree.getroot()

            # Das XML-Format der Herrnhuter Losungen
            for losung_elem in root.findall(".//Losung"):
                losung = self._parse_losung(losung_elem)
                if losung:
                    self._losungen[losung.datum] = losung

            logger.info("losungen_loaded", count=len(self._losungen))

        except ET.ParseError as e:
            logger.error("xml_parse_error", error=str(e))

    def _parse_losung(self, elem: ET.Element) -> Losung | None:
        """Parst ein einzelnes Losung-Element."""
        try:
            datum_str = elem.findtext("Datum", "")
            # Format: "2026-01-01T00:00:00" oder "2026-01-01"
            datum_part = datum_str.split("T")[0]
            datum = date.fromisoformat(datum_part)

            return Losung(
                datum=datum,
                losungstext=self._clean_text(elem.findtext("Losungstext", "")),
                losungsvers=self._clean_text(elem.findtext("Losungsvers", "")),
                lehrtext=self._clean_text(elem.findtext("Lehrtext", "")),
                lehrtextvers=self._clean_text(elem.findtext("Lehrtextvers", "")),
            )
        except (ValueError, AttributeError) as e:
            logger.warning("losung_parse_error", error=str(e))
            return None

    def _clean_text(self, text: str) -> str:
        """Bereinigt Text von überflüssigen Leerzeichen."""
        return " ".join(text.split()).strip()

    def get_losung(self, datum: date | None = None) -> Losung | None:
        """Gibt die Losung für ein bestimmtes Datum zurück."""
        if datum is None:
            datum = date.today()

        losung = self._losungen.get(datum)
        if losung:
            logger.info("losung_found", datum=datum.isoformat())
        else:
            logger.warning("losung_not_found", datum=datum.isoformat())

        return losung

    def get_today(self) -> Losung | None:
        """Gibt die heutige Losung zurück."""
        return self.get_losung(date.today())
