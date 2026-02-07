"""Tests für den Mention-Handler."""

import pytest

from losungs_bot.mention_handler import MentionHandler


class TestCommandDetection:
    """Tests für die Befehlserkennung."""

    @pytest.fixture
    def handler(self):
        """Erstellt einen MentionHandler ohne Dependencies."""
        # Handler mit None-Mocks erstellen
        handler = object.__new__(MentionHandler)
        handler.COMMANDS = MentionHandler.COMMANDS
        return handler

    def test_detect_hilfe(self, handler):
        assert handler._detect_command("hilfe") == "help"

    def test_detect_help(self, handler):
        assert handler._detect_command("help") == "help"

    def test_detect_question_mark(self, handler):
        assert handler._detect_command("?") == "help"

    def test_detect_losung(self, handler):
        assert handler._detect_command("losung") == "verse_today"

    def test_detect_heute(self, handler):
        assert handler._detect_command("heute") == "verse_today"

    def test_detect_zufall(self, handler):
        assert handler._detect_command("zufall") == "verse_random"

    def test_detect_quiz(self, handler):
        assert handler._detect_command("quiz") == "quiz"

    def test_detect_unknown(self, handler):
        assert handler._detect_command("unbekannt") is None

    def test_detect_in_sentence(self, handler):
        assert handler._detect_command("zeig mir die losung bitte") == "verse_today"


class TestVersePattern:
    """Tests für die Bibelstellen-Erkennung."""

    def test_simple_verse(self):
        match = MentionHandler.VERSE_PATTERN.search("Johannes 3,16")
        assert match is not None
        assert match.group(2) == "Johannes"
        assert match.group(3) == "3"
        assert match.group(4) == "16"

    def test_numbered_book(self):
        match = MentionHandler.VERSE_PATTERN.search("1. Mose 1,1")
        assert match is not None
        assert match.group(1) == "1. "
        assert match.group(2) == "Mose"
        assert match.group(3) == "1"
        assert match.group(4) == "1"

    def test_verse_range(self):
        match = MentionHandler.VERSE_PATTERN.search("Römer 8,28-30")
        assert match is not None
        assert match.group(2) == "Römer"
        assert match.group(4) == "28"
        assert match.group(5) == "30"

    def test_with_colon(self):
        match = MentionHandler.VERSE_PATTERN.search("Psalm 23:1")
        assert match is not None
        assert match.group(2) == "Psalm"
        assert match.group(3) == "23"
        assert match.group(4) == "1"

    def test_in_sentence(self):
        match = MentionHandler.VERSE_PATTERN.search("Kannst du mir Joh 3,16 zeigen?")
        assert match is not None
        assert match.group(2) == "Joh"

    def test_second_samuel(self):
        match = MentionHandler.VERSE_PATTERN.search("2. Samuel 7,12")
        assert match is not None
        assert match.group(1) == "2. "
        assert match.group(2) == "Samuel"

    def test_no_match(self):
        match = MentionHandler.VERSE_PATTERN.search("Hallo Welt")
        assert match is None


class TestHtmlStripping:
    """Tests für HTML-Stripping."""

    @pytest.fixture
    def handler(self):
        handler = object.__new__(MentionHandler)
        return handler

    def test_simple_html(self, handler):
        result = handler._strip_html("<p>Hallo Welt</p>")
        assert result == "Hallo Welt"

    def test_link_html(self, handler):
        result = handler._strip_html('<a href="test">Link</a>')
        assert result == "Link"

    def test_multiple_tags(self, handler):
        result = handler._strip_html("<p>Zeile 1</p><p>Zeile 2</p>")
        assert "Zeile 1" in result
        assert "Zeile 2" in result

    def test_nested_tags(self, handler):
        result = handler._strip_html("<div><span>Text</span></div>")
        assert result == "Text"

    def test_whitespace_normalization(self, handler):
        result = handler._strip_html("<p>Viel   Platz</p>")
        assert result == "Viel Platz"


class TestMentionRemoval:
    """Tests für Mention-Entfernung."""

    @pytest.fixture
    def handler(self):
        handler = object.__new__(MentionHandler)
        return handler

    def test_simple_mention(self, handler):
        result = handler._remove_mentions("@user Hallo")
        assert result.strip() == "Hallo"

    def test_federated_mention(self, handler):
        result = handler._remove_mentions("@user@mastodon.social Hallo")
        assert result.strip() == "Hallo"

    def test_multiple_mentions(self, handler):
        result = handler._remove_mentions("@user1 @user2 Hallo")
        assert result.strip() == "Hallo"

    def test_no_mention(self, handler):
        result = handler._remove_mentions("Hallo Welt")
        assert result == "Hallo Welt"

    def test_mention_at_end(self, handler):
        result = handler._remove_mentions("Hallo @user")
        assert result.strip() == "Hallo"
