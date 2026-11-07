"""Offline tests for goose video extraction."""

from unittest import TestCase, main as unittest_main

from goose.article import Article
from goose.configuration import Configuration
from goose.parsers import Parser
from goose.videos.extractors import VideoExtractor


class TestVideoExtraction(TestCase):
    def test_html5_video_source_is_extracted_and_made_absolute(self):
        article = Article()
        article.final_url = "https://news.example/world/story"
        article.top_node = Parser.fromstring("""<div>
          <video controls width="640" height="360">
            <source src="media/report.mp4" type="video/mp4">
          </video>
        </div>""")

        VideoExtractor(article, Configuration()).get_videos()

        self.assertEqual(len(article.movies), 1)
        self.assertEqual(article.movies[0].provider, "html5")
        self.assertEqual(
            article.movies[0].src, "https://news.example/world/media/report.mp4"
        )
        self.assertIn("<video", article.movies[0].embed_code)


if __name__ == "__main__":
    unittest_main()
