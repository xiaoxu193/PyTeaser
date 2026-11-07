"""Offline tests for goose URL helpers."""

from unittest import TestCase, main as unittest_main

from goose.utils import BuildURL


class TestURLHelpers(TestCase):
    def test_build_url_resolves_relative_path(self):
        self.assertEqual(
            BuildURL("media/report.mp4", "https://news.example/world/story").getUrl(),
            "https://news.example/world/media/report.mp4",
        )

    def test_build_url_keeps_absolute_url(self):
        self.assertEqual(
            BuildURL("https://cdn.example/media.mp4").getUrl(),
            "https://cdn.example/media.mp4",
        )


if __name__ == "__main__":
    unittest_main()
