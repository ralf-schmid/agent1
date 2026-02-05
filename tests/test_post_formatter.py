"""Tests für die Post-Formatierung."""

from datetime import date

import pytest

from losungs_bot.bible_links import BibleLinkGenerator
from losungs_bot.losungen import Losung
from losungs_bot.post_formatter import PostFormatter


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


class TestPostFormatter:
    def test_format_includes_emojis(self, formatter: PostFormatter, sample_losung: Losung):
        post = formatter.format_post(sample_losung)
        assert "📖" in post
        assert "✨" in post
        assert "💫" in post
        assert "🔗" in post

    def test_format_includes_verses(self, formatter: PostFormatter, sample_losung: Losung):
        post = formatter.format_post(sample_losung)
        assert "Psalm 145,18" in post
        assert "Matthäus 7,7" in post

    def test_format_includes_links(self, formatter: PostFormatter, sample_losung: Losung):
        post = formatter.format_post(sample_losung)
        assert "bibleserver.com/ELB/" in post

    def test_format_includes_hashtags(self, formatter: PostFormatter, sample_losung: Losung):
        post = formatter.format_post(sample_losung)
        assert "#DieLosungen" in post
        assert "#Bibel" in post
        assert "#Herrnhut" in post

    def test_format_includes_copyright(self, formatter: PostFormatter, sample_losung: Losung):
        """Prüft Copyright-Hinweis gemäß Nutzungsbedingungen losungen.de."""
        post = formatter.format_post(sample_losung)
        assert "© Evangelische Brüder-Unität – Herrnhuter Brüdergemeine" in post
        assert "herrnhuter.de" in post
        assert "losungen.de" in post

    def test_format_uses_correct_name(self, formatter: PostFormatter, sample_losung: Losung):
        """Prüft, dass 'Die Losungen' als Name verwendet wird."""
        post = formatter.format_post(sample_losung)
        assert "Die Losungen" in post

    def test_format_within_character_limit(
        self, formatter: PostFormatter, sample_losung: Losung
    ):
        post = formatter.format_post(sample_losung)
        assert formatter.validate_length(post, max_length=500)

    def test_format_date_german(self, formatter: PostFormatter):
        date_str = formatter._format_date(date(2026, 2, 5))
        assert date_str == "5. Februar 2026"
