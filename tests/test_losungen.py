"""Tests für den Losungen-Parser."""

import tempfile
from datetime import date
from pathlib import Path

import pytest

from losungs_bot.losungen import Losung, LosungenParser

# Sample XML im losungen.de Format
SAMPLE_XML = """<?xml version="1.0" encoding="utf-8"?>
<FreeXml>
  <Losungen>
    <Datum>2026-01-15T00:00:00</Datum>
    <Losungstext>Der HERR ist mein Hirte, mir wird nichts mangeln.</Losungstext>
    <Losungsvers>Psalm 23,1</Losungsvers>
    <Lehrtext>Jesus spricht: Ich bin der gute Hirte.</Lehrtext>
    <Lehrtextvers>Johannes 10,11</Lehrtextvers>
  </Losungen>
  <Losungen>
    <Datum>2026-01-16T00:00:00</Datum>
    <Losungstext>Fürchte dich nicht, ich bin mit dir.</Losungstext>
    <Losungsvers>Jesaja 41,10</Losungsvers>
    <Lehrtext>Gott ist Liebe.</Lehrtext>
    <Lehrtextvers>1. Johannes 4,8</Lehrtextvers>
  </Losungen>
</FreeXml>
"""

# Alternatives Format mit <Losung> (singular)
ALTERNATIVE_XML = """<?xml version="1.0" encoding="utf-8"?>
<Losungen>
  <Losung>
    <Datum>2026-02-01</Datum>
    <Losungstext>Gott ist unsere Zuversicht und Stärke.</Losungstext>
    <Losungsvers>Psalm 46,2</Losungsvers>
    <Lehrtext>Im Anfang war das Wort.</Lehrtext>
    <Lehrtextvers>Johannes 1,1</Lehrtextvers>
  </Losung>
</Losungen>
"""


class TestLosungDataclass:
    """Tests für das Losung-Dataclass."""

    def test_create_losung(self):
        losung = Losung(
            datum=date(2026, 1, 15),
            losungstext="Der HERR ist mein Hirte.",
            losungsvers="Psalm 23,1",
            lehrtext="Jesus spricht: Ich bin der gute Hirte.",
            lehrtextvers="Johannes 10,11",
        )
        assert losung.datum == date(2026, 1, 15)
        assert losung.losungsvers == "Psalm 23,1"


class TestLosungenParser:
    """Tests für den XML-Parser."""

    @pytest.fixture
    def xml_file(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml", delete=False, encoding="utf-8"
        ) as f:
            f.write(SAMPLE_XML)
            path = Path(f.name)
        yield path
        path.unlink()

    @pytest.fixture
    def alt_xml_file(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml", delete=False, encoding="utf-8"
        ) as f:
            f.write(ALTERNATIVE_XML)
            path = Path(f.name)
        yield path
        path.unlink()

    def test_load_single_file(self, xml_file):
        parser = LosungenParser(xml_file)
        losung = parser.get_losung(date(2026, 1, 15))
        assert losung is not None
        assert losung.losungstext == "Der HERR ist mein Hirte, mir wird nichts mangeln."
        assert losung.losungsvers == "Psalm 23,1"

    def test_load_multiple_entries(self, xml_file):
        parser = LosungenParser(xml_file)
        losung1 = parser.get_losung(date(2026, 1, 15))
        losung2 = parser.get_losung(date(2026, 1, 16))
        assert losung1 is not None
        assert losung2 is not None
        assert losung1.losungsvers != losung2.losungsvers

    def test_losung_not_found(self, xml_file):
        parser = LosungenParser(xml_file)
        losung = parser.get_losung(date(2099, 12, 31))
        assert losung is None

    def test_alternative_format(self, alt_xml_file):
        parser = LosungenParser(alt_xml_file)
        losung = parser.get_losung(date(2026, 2, 1))
        assert losung is not None
        assert losung.losungsvers == "Psalm 46,2"

    def test_datetime_format(self, xml_file):
        """Test dass Datum mit Zeit korrekt geparst wird."""
        parser = LosungenParser(xml_file)
        losung = parser.get_losung(date(2026, 1, 15))
        assert losung is not None
        assert losung.datum == date(2026, 1, 15)


class TestLosungenParserDirectory:
    """Tests für das Laden aus Verzeichnissen."""

    @pytest.fixture
    def temp_directory(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_load_from_directory(self, temp_directory):
        # Datei mit Losungen-Muster erstellen
        xml_file = temp_directory / "Losungen Free 2026.xml"
        xml_file.write_text(SAMPLE_XML, encoding="utf-8")

        parser = LosungenParser(temp_directory)
        losung = parser.get_losung(date(2026, 1, 15))
        assert losung is not None

    def test_load_multiple_files(self, temp_directory):
        # Zwei Dateien für verschiedene Jahre
        file1 = temp_directory / "Losungen Free 2026.xml"
        file1.write_text(SAMPLE_XML, encoding="utf-8")

        file2 = temp_directory / "Losungen Free 2027.xml"
        file2.write_text(
            SAMPLE_XML.replace("2026-01-15", "2027-01-15").replace(
                "2026-01-16", "2027-01-16"
            ),
            encoding="utf-8",
        )

        parser = LosungenParser(temp_directory)
        losung_2026 = parser.get_losung(date(2026, 1, 15))
        losung_2027 = parser.get_losung(date(2027, 1, 15))
        assert losung_2026 is not None
        assert losung_2027 is not None

    def test_empty_directory(self, temp_directory):
        parser = LosungenParser(temp_directory)
        losung = parser.get_losung(date(2026, 1, 15))
        assert losung is None


class TestTextCleaning:
    """Tests für die Text-Bereinigung."""

    @pytest.fixture
    def parser(self):
        # Parser mit nicht-existierender Datei (für _clean_text Zugriff)
        parser = object.__new__(LosungenParser)
        return parser

    def test_clean_whitespace(self, parser):
        result = parser._clean_text("Viel    Platz    hier")
        assert result == "Viel Platz hier"

    def test_clean_newlines(self, parser):
        result = parser._clean_text("Zeile 1\n  Zeile 2")
        assert result == "Zeile 1 Zeile 2"

    def test_clean_tabs(self, parser):
        result = parser._clean_text("Mit\tTab")
        assert result == "Mit Tab"

    def test_strip_edges(self, parser):
        result = parser._clean_text("  Text mit Leerzeichen  ")
        assert result == "Text mit Leerzeichen"

    def test_empty_string(self, parser):
        result = parser._clean_text("")
        assert result == ""
