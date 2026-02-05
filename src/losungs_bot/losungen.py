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
        """Lädt und parst die XML-Datei(en)."""
        # Prüfe ob der Pfad ein Verzeichnis ist oder eine einzelne Datei
        if self.xml_path.is_dir():
            self._load_from_directory(self.xml_path)
        elif self.xml_path.exists():
            self._load_file(self.xml_path)
        else:
            # Versuche das übergeordnete Verzeichnis nach Losungen-Dateien zu durchsuchen
            parent_dir = self.xml_path.parent
            if parent_dir.exists():
                self._load_from_directory(parent_dir)
            else:
                logger.warning("losungen_path_not_found", path=str(self.xml_path))

    def _load_from_directory(self, directory: Path) -> None:
        """Lädt alle Losungen-XML-Dateien aus einem Verzeichnis."""
        # Suche nach verschiedenen Dateinamen-Mustern
        patterns = [
            "Losungen Free *.xml",
            "Losungen*.xml",
            "losungen*.xml",
            "losungen.xml",
        ]

        logger.debug(
            "searching_losungen_directory",
            directory=str(directory),
            patterns=patterns,
        )

        # Debug: Zeige alle Dateien im Verzeichnis
        all_files = list(directory.glob("*"))
        logger.debug(
            "directory_contents",
            files=[f.name for f in all_files],
        )

        loaded_files = []
        for pattern in patterns:
            matching = list(directory.glob(pattern))
            if matching:
                logger.debug(
                    "pattern_matched",
                    pattern=pattern,
                    files=[f.name for f in matching],
                )
            for xml_file in matching:
                if xml_file not in loaded_files:
                    self._load_file(xml_file)
                    loaded_files.append(xml_file)

        if not loaded_files:
            logger.warning("no_losungen_files_found", directory=str(directory))
        else:
            logger.info(
                "losungen_directory_loaded",
                files=[f.name for f in loaded_files],
                total_entries=len(self._losungen),
            )

    def _load_file(self, xml_file: Path) -> None:
        """Lädt und parst eine einzelne XML-Datei."""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            count_before = len(self._losungen)

            # Suche nach Losung-Elementen mit verschiedenen Schreibweisen
            losung_elements = []

            # Format 1: <Losung> (singular) - älteres Format
            losung_elements.extend(root.findall(".//Losung"))

            # Format 2: <Losungen> (plural) - aktuelles losungen.de Format
            # Hier ist jedes <Losungen>-Element ein Tageseintrag mit Datum, Losungstext, etc.
            if not losung_elements:
                for elem in root.findall(".//Losungen"):
                    # Prüfe ob dieses Element die Tagesfelder direkt enthält
                    if elem.find("Datum") is not None:
                        losung_elements.append(elem)

            # Format 3: Kleingeschrieben
            if not losung_elements:
                losung_elements.extend(root.findall(".//losung"))
                for elem in root.findall(".//losungen"):
                    if elem.find("Datum") is not None:
                        losung_elements.append(elem)

            # Debug: Zeige die Root- und Kind-Elemente wenn nichts gefunden
            if not losung_elements:
                children = [child.tag for child in root]
                logger.warning(
                    "no_losung_elements_found",
                    file=xml_file.name,
                    root_tag=root.tag,
                    child_tags=children[:5],
                )
                all_tags = {elem.tag for elem in root.iter()}
                logger.debug("xml_all_tags", tags=sorted(all_tags))

            for losung_elem in losung_elements:
                losung = self._parse_losung(losung_elem)
                if losung:
                    self._losungen[losung.datum] = losung

            count_added = len(self._losungen) - count_before
            logger.info("losungen_file_loaded", file=xml_file.name, entries=count_added)

        except ET.ParseError as e:
            logger.error("xml_parse_error", file=xml_file.name, error=str(e))

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
