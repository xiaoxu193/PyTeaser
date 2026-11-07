"""Offline tests for Goose article extraction."""

from types import SimpleNamespace
from unittest import TestCase, main as unittest_main
from unittest.mock import patch

from goose import Goose
from goose.crawler import Crawler
from goose.network import FetchError, HtmlFetcher
from pyteaser import (
    ArticleExtractionError,
    ArticleFetchError,
    SummarizeUrl,
    summarize_url,
)


class TestGooseExtraction(TestCase):
    def test_extracts_article_from_raw_html_without_network(self):
        html = """<html lang="en"><head><title>Test article</title></head>
        <body><article>
          <p>This is a substantial first paragraph about Python compatibility, café culture, and article extraction.</p>
          <p>This is another substantial paragraph with enough useful words to pass the content filters.</p>
        </article></body></html>"""

        article = Goose({"enable_image_fetching": False}).extract(
            raw_html=html.encode("utf-8")
        )

        self.assertEqual(article.title, "Test article")
        self.assertIn("Python compatibility", article.cleaned_text)
        self.assertIn("café culture", article.cleaned_text)

    def test_summarize_url_with_mocked_response(self):
        html = b"""<html lang="en"><head><title>Example article title</title></head>
        <body><article>
          <p>Researchers announced a new discovery after years of careful work. The team shared detailed results with the public.</p>
          <p>Independent experts reviewed the findings and confirmed the core measurements. The discovery may lead to useful new technology.</p>
          <p>Further studies are planned for next year. Researchers said the work is still preliminary.</p>
        </article></body></html>"""

        with patch.object(HtmlFetcher, "get_html", return_value=html):
            summaries = SummarizeUrl("https://example.test/article")

        self.assertEqual(len(summaries), 5)
        self.assertTrue(all(isinstance(sentence, str) for sentence in summaries))

    def test_summarize_url_honors_sentence_count(self):
        html = b"""<html lang="en"><head><title>Example article title</title></head>
        <body><article><p>One sentence is here. Two sentence is here. Three sentence is here.
        Four sentence is here. Five sentence is here. Six sentence is here.</p></article></body></html>"""

        with patch.object(HtmlFetcher, "get_html", return_value=html):
            summaries = SummarizeUrl("https://example.test/article", sentence_count=2)

        self.assertEqual(len(summaries), 2)

    def test_summarize_url_uses_article_language_metadata(self):
        article = SimpleNamespace(
            title="Articulo de ejemplo",
            cleaned_text="El gobierno anuncia una nueva reforma.",
            meta_lang="es",
        )

        with patch("pyteaser.grab_link", return_value=article):
            with patch("pyteaser.Summarize", return_value=["resumen"]) as summarize:
                result = SummarizeUrl("https://example.test/articulo")

        self.assertEqual(result, ["resumen"])
        self.assertEqual(summarize.call_args.kwargs["language"], "es")

    def test_pep8_url_api_forwards_options(self):
        article = SimpleNamespace(
            title="Example article",
            cleaned_text="Researchers announced a discovery. Experts reviewed evidence.",
            meta_lang="en",
        )

        with patch("pyteaser.grab_link", return_value=article):
            summaries = summarize_url(
                "https://example.test/article", sentence_count=1, max_words=10
            )

        self.assertEqual(len(summaries), 1)

    def test_url_fetch_failure_raises_public_exception(self):
        with patch("pyteaser.grab_link", side_effect=FetchError("blocked")):
            with self.assertRaises(ArticleFetchError):
                SummarizeUrl("https://example.test/article")

    def test_missing_article_content_raises_public_exception(self):
        article = SimpleNamespace(title="", cleaned_text="Some text", meta_lang="en")

        with patch("pyteaser.grab_link", return_value=article):
            with self.assertRaises(ArticleExtractionError):
                SummarizeUrl("https://example.test/article")

    def test_private_image_url_is_skipped_without_failing_extraction(self):
        html = """<html><head><title>Image fetch test</title></head><body><article>
          <p>This is a sufficiently long paragraph about article extraction, safe network handling, and testing.</p>
          <img src="http://127.0.0.1/private.jpg" alt="local image">
          <p>This is another sufficiently long paragraph so the body can be recognized correctly by Goose.</p>
        </article></body></html>"""

        article = Goose({"enable_image_fetching": True}).extract(raw_html=html)

        self.assertEqual(article.title, "Image fetch test")
        self.assertIn("safe network handling", article.cleaned_text)

    def test_image_fetching_is_disabled_by_default(self):
        html = """<html><head><title>No image fetch</title></head><body><article>
          <p>This is a sufficiently long paragraph about ordinary article extraction and summaries.</p>
          <img src="https://1.1.1.1/image.jpg" alt="remote image">
          <p>This second sufficiently long paragraph provides another useful extraction candidate.</p>
        </article></body></html>"""

        with patch.object(Crawler, "get_image_extractor") as get_image_extractor:
            article = Goose().extract(raw_html=html)

        get_image_extractor.assert_not_called()
        self.assertEqual(article.title, "No image fetch")

    def test_custom_metadata_extractors_are_invoked(self):
        class PublishDateExtractor:
            def extract(self, document):
                return "2025-02-03"

        class AdditionalDataExtractor:
            def extract(self, document):
                return {"section": "science", "reviewed": True}

        html = """<html><head><title>Metadata extraction test</title></head>
        <body><article>
          <p>This sufficiently long paragraph validates article metadata extractor hooks.</p>
          <p>This second long paragraph ensures standard article content is still extracted.</p>
        </article></body></html>"""
        article = Goose(
            {
                "enable_image_fetching": False,
                "extract_publishdate": PublishDateExtractor(),
                "additional_data_extractor": AdditionalDataExtractor(),
            }
        ).extract(raw_html=html)

        self.assertEqual(article.publish_date, "2025-02-03")
        self.assertEqual(
            article.additional_data,
            {
                "section": "science",
                "reviewed": True,
            },
        )

    def test_publication_date_is_extracted_from_article_meta(self):
        html = """<html><head>
          <title>Published article</title>
          <meta property="article:published_time" content="2025-04-05T12:30:00Z">
        </head><body><article>
          <p>This sufficiently long paragraph supports extraction of publication metadata.</p>
          <p>This second paragraph ensures Goose recognizes the main article body.</p>
        </article></body></html>"""

        article = Goose({"enable_image_fetching": False}).extract(raw_html=html)

        self.assertEqual(article.publish_date, "2025-04-05T12:30:00Z")

    def test_publication_date_falls_back_to_json_ld(self):
        html = """<html><head><title>Structured article</title>
          <script type="application/ld+json">
            {"@graph": [{"@type": "NewsArticle", "datePublished": "2025-06-07"}]}
          </script>
        </head><body><article>
          <p>This sufficiently long paragraph supports extraction of structured metadata.</p>
          <p>This second paragraph ensures the content pipeline continues normally.</p>
        </article></body></html>"""

        article = Goose({"enable_image_fetching": False}).extract(raw_html=html)

        self.assertEqual(article.publish_date, "2025-06-07")

    def test_open_graph_title_is_used_when_document_title_is_missing(self):
        html = """<html><head>
          <meta property="og:title" content="Open Graph article title">
        </head><body><article>
          <p>This sufficiently long paragraph allows Goose to extract the article body.</p>
          <p>This second paragraph continues to provide meaningful article content.</p>
        </article></body></html>"""

        article = Goose({"enable_image_fetching": False}).extract(raw_html=html)

        self.assertEqual(article.title, "Open Graph article title")

    def test_json_ld_headline_is_used_when_document_title_is_missing(self):
        html = """<html><head>
          <script type="application/ld+json">
            {"@type":"NewsArticle","headline":"Structured article headline"}
          </script>
        </head><body><article>
          <p>This sufficiently long paragraph allows Goose to extract the article body.</p>
          <p>This second paragraph continues to provide meaningful article content.</p>
        </article></body></html>"""

        article = Goose({"enable_image_fetching": False}).extract(raw_html=html)

        self.assertEqual(article.title, "Structured article headline")


if __name__ == "__main__":
    unittest_main()
