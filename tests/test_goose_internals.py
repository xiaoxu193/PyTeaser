"""Offline tests for Goose language selection and initialization."""

import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest import TestCase, main as unittest_main
from unittest.mock import patch

from goose import Goose
from goose.article import Article
from goose.configuration import Configuration
from goose.extractors import StandardContentExtractor
from goose.text import StopWords, StopWordsChinese, stopwords_class_for_language


class TestGooseLanguageSelection(TestCase):
    def test_metadata_language_is_used_for_content_scoring(self):
        config = Configuration()
        article = Article()
        article.meta_lang = "es-MX"
        extractor = StandardContentExtractor(config)
        extractor.nodes_to_check = lambda doc: []

        extractor.calculate_best_node(article)

        self.assertEqual(extractor.language, "es")

    def test_configured_language_overrides_metadata_when_forced(self):
        config = Configuration()
        config.use_meta_language = False
        config.target_language = "fr"
        article = Article()
        article.meta_lang = "es"
        extractor = StandardContentExtractor(config)

        self.assertEqual(extractor.get_language(article), "fr")

    def test_chinese_metadata_selects_character_aware_stopwords(self):
        extractor = StandardContentExtractor(Configuration())
        extractor.language = "zh"

        with patch.dict("sys.modules", {"jieba": None}):
            stats = extractor.get_word_stats("研究者在这里")

        self.assertEqual(stats.get_word_count(), 6)
        self.assertGreater(stats.get_stopword_count(), 0)
        self.assertIs(
            stopwords_class_for_language("zh", StopWords), StopWordsChinese)


class TestGooseInitialization(TestCase):
    def test_concurrent_initialization_uses_unique_write_probes(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            storage_path = os.path.join(temporary_directory, "nested", "goose")
            config = SimpleNamespace(local_storage_path=storage_path)

            with ThreadPoolExecutor(max_workers=8) as executor:
                instances = list(executor.map(lambda _: Goose(config), range(16)))

            self.assertEqual(len(instances), 16)
            self.assertTrue(os.path.isdir(storage_path))
            self.assertFalse(os.path.exists(os.path.join(storage_path, "test.txt")))




if __name__ == '__main__':
    unittest_main()
