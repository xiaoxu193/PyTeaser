"""Offline tests for goose image extraction and file safety."""

import os
import tempfile
from importlib.util import find_spec
from types import SimpleNamespace
from unittest import TestCase
from unittest import main as unittest_main
from unittest.mock import patch

from goose.article import Article
from goose.configuration import Configuration
from goose.images.extractors import KNOWN_IMG_DOM_NAMES, UpgradedImageIExtractor
from goose.images.image import ImageDetails, LocallyStoredImage
from goose.images.utils import ImageUtils
from goose.parsers import Parser


class TestImageExtraction(TestCase):
    def setUp(self):
        self.config = Configuration()
        self.config.images_min_bytes = 100
        self.config.max_image_bytes = 1000
        self.article = Article()
        self.article.final_url = "https://news.example/article"
        self.article.domain = "news.example"
        self.article.link_hash = "test-article"
        self.article.raw_doc = Parser.fromstring("<html><body></body></html>")
        self.extractor = UpgradedImageIExtractor(None, self.article, self.config)

    def test_configured_image_byte_limits_are_used(self):
        document = Parser.fromstring(
            '<html><body><img src="https://news.example/image.jpg"></body></html>'
        )
        image_node = Parser.getElementsByTag(document, tag="img")[0]
        too_small = LocallyStoredImage(
            src="https://news.example/image.jpg",
            bytes=100,
            width=100,
            height=100,
            file_extension=".jpg",
        )
        accepted = LocallyStoredImage(
            src="https://news.example/image.jpg",
            bytes=101,
            width=100,
            height=100,
            file_extension=".jpg",
        )

        with patch.object(self.extractor, "get_local_image", return_value=too_small):
            self.assertIsNone(self.extractor.get_images_bytesize_match([image_node]))
        with patch.object(self.extractor, "get_local_image", return_value=accepted):
            self.assertEqual(
                self.extractor.get_images_bytesize_match([image_node]), [image_node]
            )

    def test_gif_and_unknown_formats_are_not_scored_as_article_images(self):
        document = Parser.fromstring("""<html><body>
          <img src="https://news.example/animation.gif">
          <img src="https://news.example/unknown">
          <img src="https://news.example/photo.jpg">
        </body></html>""")
        image_nodes = Parser.getElementsByTag(document, tag="img")
        local_images = [
            LocallyStoredImage(
                src="https://news.example/animation.gif",
                bytes=5000,
                width=100,
                height=100,
                file_extension=".gif",
            ),
            LocallyStoredImage(
                src="https://news.example/unknown",
                bytes=5000,
                width=100,
                height=100,
                file_extension="NA",
            ),
            LocallyStoredImage(
                src="https://news.example/photo.jpg",
                bytes=5000,
                width=100,
                height=100,
                file_extension=".jpg",
            ),
        ]

        with patch.object(self.extractor, "get_local_image", side_effect=local_images):
            scored_images = self.extractor.fetch_images(image_nodes, 0)

        self.assertEqual(
            [image.src for image in scored_images],
            [
                "https://news.example/photo.jpg",
            ],
        )

    def test_invalid_image_dimensions_are_rejected(self):
        self.assertTrue(self.extractor.is_banner_dimensions(0, 100))
        self.assertTrue(self.extractor.is_banner_dimensions(100, 0))

    def test_site_specific_selectors_do_not_mutate_global_defaults(self):
        defaults = list(KNOWN_IMG_DOM_NAMES)
        self.article.domain = "custom.example"
        self.article.raw_doc = Parser.fromstring("""<html><body>
          <div class="custom-thumbnail"><img src="https://custom.example/photo.jpg"></div>
        </body></html>""")
        self.extractor.custom_site_mapping["custom.example"] = "custom-thumbnail"

        with patch.object(self.extractor, "get_image", return_value="matched"):
            result = self.extractor.check_known_elements()

        self.assertEqual(result, "matched")
        self.assertEqual(KNOWN_IMG_DOM_NAMES, defaults)

    def test_webp_format_has_a_recognized_extension(self):
        image_details = ImageDetails()
        image_details.set_mime_type("WEBP")
        self.assertEqual(ImageUtils.get_mime_type(image_details), ".webp")

    def test_lazy_image_and_srcset_urls_are_supported(self):
        document = Parser.fromstring("""<html><body>
          <img src="/placeholder.gif" data-src="/lazy.jpg"
               srcset="/small.jpg 320w, /large.jpg 2x">
          <img data-src="data:image/png;base64,AAAA">
        </body></html>""")
        image_nodes = Parser.getElementsByTag(document, tag="img")

        self.assertEqual(self.extractor.get_image_src(image_nodes[0]), "/large.jpg")
        self.assertTrue(self.extractor.is_valid_filename(image_nodes[0]))
        self.assertIsNone(self.extractor.get_image_src(image_nodes[1]))


class TestImageFileSafety(TestCase):
    def test_cached_oversized_image_is_rejected_before_decode(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            config = SimpleNamespace(
                local_storage_path=temporary_directory,
                max_image_bytes=4,
            )
            src = "https://1.1.1.1/large.jpg"
            local_path = ImageUtils.get_localfile_name("article", src, config)
            with open(local_path, "wb") as image_file:
                image_file.write(b"too large")

            with patch.object(ImageUtils, "get_image_dimensions") as get_dimensions:
                image = ImageUtils.read_localfile("article", src, config)

        self.assertIsNone(image)
        get_dimensions.assert_not_called()

    def test_invalid_downloaded_image_is_discarded(self):
        if find_spec("PIL") is None:
            self.skipTest("Pillow is required to test image decoding")

        with tempfile.TemporaryDirectory() as temporary_directory:
            config = SimpleNamespace(
                local_storage_path=temporary_directory,
                max_image_bytes=100,
                request_timeout=1,
                allow_private_network=False,
                browser_user_agent="PyTeaser test",
            )
            src = "https://1.1.1.1/not-an-image.jpg"
            local_path = ImageUtils.get_localfile_name("article", src, config)
            with patch("goose.images.utils.fetch_bytes", return_value=b"not image"):
                image = ImageUtils.store_image(None, "article", src, config)

        self.assertIsNone(image)
        self.assertFalse(os.path.exists(local_path))


if __name__ == "__main__":
    unittest_main()
