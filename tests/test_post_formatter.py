"""Tests für die Post-Formatierung."""

from datetime import date

import pytest

from losungs_bot.bible_links import BibleLinkGenerator
from losungs_bot.losungen import Losung
from losungs_bot.post_formatter import FormattedPost, PostFormatter


@pytest.fixture
def formatter() -> PostFormatter:
    generator = BibleLinkGenerator(
        base_url="https://www.bibleserver.com",
        translation="ELB",
    )
    return PostFormatter(generator)


@pytest.fixture
def sample_losung() -> Losung:
    return Losung(
        datum=date(2026, 2, 5),
        losungstext="Der HERR ist nahe allen, die ihn anrufen.",
        losungsvers="Psalm 145,18",
        lehrtext="Bittet, so wird euch gegeben.",
        lehrtextvers="Matthäus 7,7",
    )


@pytest.fixture
def long_losung() -> Losung:
    """Eine Losung die zu lang für einen einzelnen Post ist, aber nach Split passt."""
    return Losung(
        datum=date(2026, 2, 6),
        losungstext="Der HERR ist mein Hirte, mir wird nichts mangeln. "
        "Er weidet mich auf einer grünen Aue und führet mich zum frischen Wasser.",
        losungsvers="Psalm 23,1-2",
        lehrtext="Denn also hat Gott die Welt geliebt, dass er seinen eingeborenen Sohn gab, "
        "auf dass alle, die an ihn glauben, nicht verloren werden, sondern das ewige Leben haben.",
        lehrtextvers="Johannes 3,16",
    )


class TestPostFormatter:
    def test_format_includes_emojis(
        self, formatter: PostFormatter, sample_losung: Losung
    ):
        formatted = formatter.format_post(sample_losung)
        assert "📖" in formatted.main_post
        assert "✨" in formatted.main_post
        assert "💫" in formatted.main_post
        assert "🔗" in formatted.main_post

    def test_format_includes_verses(
        self, formatter: PostFormatter, sample_losung: Losung
    ):
        formatted = formatter.format_post(sample_losung)
        assert "Psalm 145,18" in formatted.main_post
        assert "Matthäus 7,7" in formatted.main_post

    def test_format_includes_links(
        self, formatter: PostFormatter, sample_losung: Losung
    ):
        formatted = formatter.format_post(sample_losung)
        assert "bibleserver.com/ELB/" in formatted.main_post

    def test_format_includes_hashtags(
        self, formatter: PostFormatter, sample_losung: Losung
    ):
        formatted = formatter.format_post(sample_losung)
        # Hashtags können im Hauptpost oder in der Antwort sein
        all_content = formatted.main_post
        if formatted.copyright_reply:
            all_content += formatted.copyright_reply
        assert "#DieLosungen" in all_content
        assert "#FediKirche" in all_content
        assert "#Bibel" in all_content
        assert "#Herrnhut" in all_content

    def test_format_includes_copyright(
        self, formatter: PostFormatter, sample_losung: Losung
    ):
        """Prüft Copyright-Hinweis gemäß Nutzungsbedingungen losungen.de."""
        formatted = formatter.format_post(sample_losung)
        # Copyright kann im Hauptpost oder in der Antwort sein
        all_content = formatted.main_post
        if formatted.copyright_reply:
            all_content += formatted.copyright_reply

        assert "© Evangelische Brüder-Unität – Herrnhuter Brüdergemeine" in all_content
        assert "herrnhuter.de" in all_content
        assert "losungen.de" in all_content

    def test_format_uses_correct_name(
        self, formatter: PostFormatter, sample_losung: Losung
    ):
        """Prüft, dass 'Die Losungen' als Name verwendet wird."""
        formatted = formatter.format_post(sample_losung)
        assert "Die Losungen" in formatted.main_post

    def test_format_within_character_limit(
        self, formatter: PostFormatter, sample_losung: Losung
    ):
        formatted = formatter.format_post(sample_losung)
        assert formatter.validate_length(formatted.main_post, max_length=500)
        if formatted.copyright_reply:
            assert formatter.validate_length(formatted.copyright_reply, max_length=500)

    def test_format_date_german(self, formatter: PostFormatter):
        date_str = formatter._format_date(date(2026, 2, 5))
        assert date_str == "5. Februar 2026"

    def test_short_post_no_split(
        self, formatter: PostFormatter, sample_losung: Losung
    ):
        """Kurze Posts sollten nicht aufgeteilt werden."""
        formatted = formatter.format_post(sample_losung)
        assert not formatted.needs_reply
        assert formatted.copyright_reply is None

    def test_long_post_is_split(self, formatter: PostFormatter, long_losung: Losung):
        """Lange Posts sollten aufgeteilt werden."""
        formatted = formatter.format_post(long_losung)
        assert formatted.needs_reply
        assert formatted.copyright_reply is not None
        # Beide Posts müssen unter 500 Zeichen sein
        assert len(formatted.main_post) <= 500
        assert len(formatted.copyright_reply) <= 500

    def test_very_long_post_splits_verses(self, formatter: PostFormatter):
        """Wenn beide Verse zusammen > 500 Zeichen sind, wird weiter aufgeteilt."""
        very_long_losung = Losung(
            datum=date(2026, 2, 24),
            losungstext="Fürchte dich nicht, denn ich bin mit dir; "
            "hab keine Angst, denn ich bin dein Gott. "
            "Ich stärke dich, ja, ich helfe dir, ja, "
            "ich halte dich aufrecht mit der Rechten meiner Gerechtigkeit. "
            "Denn ich, der HERR, dein Gott, ergreife deine rechte Hand "
            "und sage zu dir: Fürchte dich nicht, ich helfe dir!",
            losungsvers="Jesaja 41,10-13",
            lehrtext="So seid nun stark und lasst eure Hände nicht sinken; "
            "denn euer Werk hat seinen Lohn.",
            lehrtextvers="2. Chronik 15,7",
        )
        formatted = formatter.format_post(very_long_losung)
        assert formatted.needs_reply
        # Hauptpost enthält nur den Losungsvers, nicht den Lehrtext
        assert "Jesaja" in formatted.main_post
        assert "Chronik" not in formatted.main_post
        # Antwort enthält den Lehrtext
        assert "Chronik" in formatted.copyright_reply
        # Beide müssen unter 500 Zeichen sein
        assert len(formatted.main_post) <= 500
        assert len(formatted.copyright_reply) <= 500

    def test_very_long_lehrtext_compact_reply(self, formatter: PostFormatter):
        """Wenn Lehrtext+Copyright > 500 Zeichen: kompakte Antwort ohne Podcasts."""
        losung = Losung(
            datum=date(2026, 2, 24),
            losungstext="Fürchte dich nicht, denn ich bin mit dir; "
            "hab keine Angst, denn ich bin dein Gott. "
            "Ich stärke dich, ja, ich helfe dir, ja, "
            "ich halte dich aufrecht mit der Rechten meiner Gerechtigkeit.",
            losungsvers="Jesaja 41,10",
            lehrtext="Denn Gott hat uns nicht gegeben den Geist der Furcht, "
            "sondern der Kraft und der Liebe und der Besonnenheit. "
            "Darum schäme dich nicht des Zeugnisses von unserm Herrn "
            "noch meiner, der ich sein Gefangener bin, sondern leide "
            "mit für das Evangelium in der Kraft Gottes.",
            lehrtextvers="2. Timotheus 1,7-8",
        )
        formatted = formatter.format_post(losung)
        assert formatted.needs_reply
        # Beide Posts müssen unter 500 Zeichen sein
        assert len(formatted.main_post) <= 500
        assert len(formatted.copyright_reply) <= 500
        # Copyright muss trotzdem enthalten sein
        assert "Herrnhuter" in formatted.copyright_reply

    def test_formatted_post_dataclass(self):
        """Test der FormattedPost Datenstruktur."""
        # Ohne Antwort
        post = FormattedPost(main_post="Test")
        assert not post.needs_reply
        assert post.copyright_reply is None

        # Mit Antwort
        post_with_reply = FormattedPost(main_post="Test", copyright_reply="Copyright")
        assert post_with_reply.needs_reply
        assert post_with_reply.copyright_reply == "Copyright"
