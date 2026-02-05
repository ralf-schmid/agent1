"""Tests für den BibleServer URL-Generator."""

import pytest

from losungs_bot.bible_links import BibleLinkGenerator


@pytest.fixture
def generator() -> BibleLinkGenerator:
    return BibleLinkGenerator(
        base_url="https://www.bibleserver.com",
        translation="ELB",
    )


class TestBibleLinkGenerator:
    def test_simple_reference(self, generator: BibleLinkGenerator):
        url = generator.generate_short_url("Psalm 145,18")
        assert url == "www.bibleserver.com/ELB/Psalm145,18"

    def test_numbered_book(self, generator: BibleLinkGenerator):
        url = generator.generate_short_url("1. Mose 1,1")
        assert url == "www.bibleserver.com/ELB/1.Mose1,1"

    def test_new_testament(self, generator: BibleLinkGenerator):
        url = generator.generate_short_url("Matthäus 7,7")
        assert url == "www.bibleserver.com/ELB/Matthäus7,7"

    def test_verse_range(self, generator: BibleLinkGenerator):
        url = generator.generate_short_url("Johannes 3,16-17")
        assert url == "www.bibleserver.com/ELB/Johannes3,16-17"

    def test_full_url(self, generator: BibleLinkGenerator):
        url = generator.generate_url("Römer 8,28")
        assert url.startswith("https://www.bibleserver.com/ELB/")
        assert "R%C3%B6mer" in url or "Römer" in url
