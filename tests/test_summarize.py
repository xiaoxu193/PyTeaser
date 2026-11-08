"""Offline tests for the summarization API."""

from types import ModuleType
from unittest import TestCase
from unittest import main as unittest_main
from unittest.mock import patch

from pyteaser import (
    ScoringWeights,
    Summarize,
    keywords,
    length_score,
    score,
    split_sentences,
    split_words,
    stopWords,
    summarize,
    summarize_detailed,
    title_score,
)


class TestSummarize(TestCase):
    def test_text(self):
        article_title = "Framework for Partitioning and Execution of Data Stream Applications in Mobile Cloud Computing"
        article_text = "The contribution of cloud computing and mobile computing technologies lead to the newly emerging mobile cloud com- puting paradigm. Three major approaches have been pro- posed for mobile cloud applications: 1) extending the access to cloud services to mobile devices; 2) enabling mobile de- vices to work collaboratively as cloud resource providers; 3) augmenting the execution of mobile applications on portable devices using cloud resources. In this paper, we focus on the third approach in supporting mobile data stream applica- tions. More specifically, we study how to optimize the com- putation partitioning of a data stream application between mobile and cloud to achieve maximum speed/throughput in processing the streaming data. To the best of our knowledge, it is the first work to study the partitioning problem for mobile data stream applica- tions, where the optimization is placed on achieving high throughput of processing the streaming data rather than minimizing the makespan of executions as in other appli- cations. We first propose a framework to provide runtime support for the dynamic computation partitioning and exe- cution of the application. Different from existing works, the framework not only allows the dynamic partitioning for a single user but also supports the sharing of computation in- stances among multiple users in the cloud to achieve efficient utilization of the underlying cloud resources. Meanwhile, the framework has better scalability because it is designed on the elastic cloud fabrics. Based on the framework, we design a genetic algorithm for optimal computation parti- tion. Both numerical evaluation and real world experiment have been performed, and the results show that the par- titioned application can achieve at least two times better performance in terms of throughput than the application without partitioning."

        summarised_article_text = [
            "The contribution of cloud computing and mobile computing technologies lead to the newly emerging mobile cloud com- puting paradigm.",
            "Three major approaches have been pro- posed for mobile cloud applications: 1) extending the access to cloud services to mobile devices; 2) enabling mobile de- vices to work collaboratively as cloud resource providers; 3) augmenting the execution of mobile applications on portable devices using cloud resources.",
            "In this paper, we focus on the third approach in supporting mobile data stream applica- tions.",
            "More specifically, we study how to optimize the com- putation partitioning of a data stream application between mobile and cloud to achieve maximum speed/throughput in processing the streaming data.",
            "We first propose a framework to provide runtime support for the dynamic computation partitioning and exe- cution of the application.",
        ]

        self.assertEqual(
            Summarize(article_title, article_text), summarised_article_text
        )

    def test_short_article_returns_its_sentences(self):
        self.assertEqual(
            Summarize("A short article.", "First sentence. Second sentence."),
            ["First sentence.", "Second sentence."],
        )

    def test_blank_text_returns_empty_summary(self):
        self.assertEqual(Summarize("Title", " \n\t "), [])

    def test_missing_title_and_utf8_bytes_are_supported(self):
        self.assertEqual(
            Summarize(None, "First sentence. Second sentence."),
            [
                "First sentence.",
                "Second sentence.",
            ],
        )
        self.assertEqual(
            Summarize("Café".encode("utf-8"), "Café matters.".encode("utf-8")),
            [
                "Café matters.",
            ],
        )

    def test_pep8_text_api_matches_legacy_name(self):
        text = "Researchers announced a discovery. Experts reviewed the evidence."
        self.assertEqual(
            summarize("Discovery", text, sentence_count=1),
            Summarize("Discovery", text, sentence_count=1),
        )

    def test_unsupported_text_types_raise_clear_errors(self):
        with self.assertRaisesRegex(TypeError, "text must be a string"):
            Summarize("Title", None)
        with self.assertRaisesRegex(TypeError, "text must be a string"):
            Summarize("Title", 42)
        with self.assertRaisesRegex(ValueError, "valid UTF-8"):
            Summarize("Title", b"\xff")

    def test_sentence_count_is_configurable(self):
        text = "One sentence. Two sentence. Three sentence. Four sentence. Five sentence. Six sentence."

        self.assertEqual(len(Summarize("Title", text)), 5)
        self.assertEqual(len(Summarize("Title", text, sentence_count=2)), 2)
        self.assertEqual(Summarize("Title", text, sentence_count=0), [])

    def test_invalid_sentence_count_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "sentence_count"):
            Summarize("Title", "Article text.", sentence_count=-1)
        with self.assertRaisesRegex(TypeError, "sentence_count"):
            Summarize("Title", "Article text.", sentence_count=1.5)
        with self.assertRaisesRegex(TypeError, "sentence_count"):
            Summarize("Title", "Article text.", sentence_count=True)

    def test_max_words_constrains_the_selected_summary(self):
        sentences = [
            "Researchers published detailed results yesterday.",
            "Experts verified results.",
        ]
        ranked = [(0, sentences[0], 10.0), (1, sentences[1], 9.0)]

        with patch("pyteaser.score", return_value=ranked):
            summary = Summarize(
                "Results", " ".join(sentences), sentence_count=2, max_words=3
            )

        self.assertEqual(summary, [sentences[1]])
        self.assertLessEqual(sum(len(split_words(sentence)) for sentence in summary), 3)

    def test_max_words_is_validated_and_can_be_zero(self):
        self.assertEqual(Summarize("Title", "Some words here.", max_words=0), [])
        with self.assertRaisesRegex(ValueError, "max_words"):
            Summarize("Title", "Some words here.", max_words=-1)
        with self.assertRaisesRegex(TypeError, "max_words"):
            Summarize("Title", "Some words here.", max_words=1.5)
        with self.assertRaisesRegex(TypeError, "max_words"):
            Summarize("Title", "Some words here.", max_words=True)

    def test_custom_scoring_weights_are_supported(self):
        ranked = score(
            ["Topic drives the result.", "Other facts matter."],
            ["topic"],
            {},
            weights=ScoringWeights(title=1.0, frequency=0.0, length=0.0, position=0.0),
        )

        self.assertEqual(ranked[0][2], 1.0)
        self.assertEqual(ranked[1][2], 0.0)

    def test_detailed_summary_reports_source_indices_and_scores(self):
        title = "Research results"
        text = (
            "Researchers announced detailed results today. "
            "Experts reviewed the independent evidence. "
            "The study has several important implications. "
            "More research is needed next year."
        )

        details = summarize_detailed(title, text, sentence_count=2)

        self.assertEqual(len(details), 2)
        self.assertTrue(all(isinstance(result.index, int) for result in details))
        self.assertTrue(all(isinstance(result.score, float) for result in details))
        self.assertEqual(
            [result.sentence for result in details],
            Summarize(title, text, sentence_count=2),
        )
        self.assertEqual(
            [result.index for result in details],
            sorted(result.index for result in details),
        )

    def test_invalid_scoring_weights_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "non-negative"):
            ScoringWeights(title=-1.0)
        with self.assertRaisesRegex(ValueError, "positive"):
            ScoringWeights(title=0, frequency=0, length=0, position=0)
        with self.assertRaisesRegex(TypeError, "numeric"):
            ScoringWeights(title=True)
        with self.assertRaisesRegex(TypeError, "title, frequency"):
            Summarize("Title", "Article text.", weights={"unknown": 1})

    def test_sentence_splitter_handles_lowercase_starts_and_quotes(self):
        self.assertEqual(
            split_sentences("First ends. lowercase follows! “Quoted?” yes."),
            ["First ends.", "lowercase follows!", "“Quoted?”", "yes."],
        )

    def test_sentence_splitter_handles_abbreviations_and_decimals(self):
        self.assertEqual(
            split_sentences(
                "Dr. Smith paid 3.14 dollars. The U.S. team met at 5 p.m. It continued."
            ),
            [
                "Dr. Smith paid 3.14 dollars.",
                "The U.S. team met at 5 p.m.",
                "It continued.",
            ],
        )

    def test_sentence_splitter_keeps_number_abbreviations_together(self):
        self.assertEqual(
            split_sentences("She chose No. 3. It worked."),
            ["She chose No. 3.", "It worked."],
        )

    def test_sentence_splitter_handles_paragraphs_and_cjk_punctuation(self):
        self.assertEqual(
            split_sentences("First paragraph\n\n这是第一句。这是第二句！"),
            ["First paragraph", "这是第一句。", "这是第二句！"],
        )

    def test_summary_restores_original_order_after_ranking(self):
        sentences = [
            "Alpha begins today.",
            "Bravo announces plans.",
            "Charlie discovers evidence.",
            "Delta publishes results.",
            "Echo reports success.",
            "Foxtrot reveals details.",
        ]
        ranked = [
            (5, sentences[5], 10.0),
            (1, sentences[1], 9.0),
            (4, sentences[4], 8.0),
            (2, sentences[2], 7.0),
            (3, sentences[3], 6.0),
            (0, sentences[0], 1.0),
        ]

        with patch("pyteaser.score", return_value=ranked):
            summary = Summarize("An article", " ".join(sentences))

        self.assertEqual(summary, sentences[1:])

    def test_summary_skips_redundant_sentences(self):
        sentences = [
            "Researchers confirmed several new findings.",
            "Researchers confirmed several new findings.",
            "The final report described four separate outcomes.",
            "Independent experts reviewed the published evidence.",
        ]
        ranked = [
            (0, sentences[0], 10.0),
            (1, sentences[1], 9.0),
            (3, sentences[3], 8.0),
            (2, sentences[2], 7.0),
        ]

        with patch("pyteaser.score", return_value=ranked):
            summary = Summarize("An article", " ".join(sentences), sentence_count=3)

        self.assertEqual(summary, [sentences[0], sentences[2], sentences[3]])

    def test_short_article_does_not_repeat_duplicate_sentences(self):
        self.assertEqual(
            Summarize(
                "A short article",
                "Researchers confirmed several findings. Researchers confirmed several findings.",
            ),
            ["Researchers confirmed several findings."],
        )

    def test_every_supported_language_has_stopwords(self):
        from pyteaser import _SUPPORTED_LANGUAGES, _load_stop_words

        for language in sorted(_SUPPORTED_LANGUAGES):
            stop_words = _load_stop_words(language)
            self.assertTrue(stop_words, "empty stopword list for %s" % language)
            self.assertTrue(
                all(word == word.casefold() for word in stop_words), language
            )

    def test_topic_words_are_not_filtered_as_stopwords(self):
        self.assertNotIn("government", stopWords)
        self.assertNotIn("police", stopWords)
        self.assertNotIn("reuters", stopWords)
        self.assertNotIn("rappler", stopWords)
        self.assertIn("government", keywords("Government police"))
        self.assertIn("police", keywords("Government police"))

    def test_language_specific_stopwords_are_used(self):
        spanish_keywords = keywords(
            "El gobierno anuncia una nueva reforma", language="es"
        )

        self.assertNotIn("el", spanish_keywords)
        self.assertNotIn("una", spanish_keywords)
        self.assertIn("gobierno", spanish_keywords)
        self.assertIn("reforma", spanish_keywords)

    def test_chinese_tokenizer_is_used_when_available(self):
        jieba = ModuleType("jieba")
        jieba.cut = lambda text: ["研究者", "公布", "新发现", "。"]

        with patch.dict("sys.modules", {"jieba": jieba}):
            words = split_words("研究者公布新发现。", language="zh")

        self.assertEqual(words, ["研究者", "公布", "新发现"])

    def test_chinese_tokenizer_falls_back_without_jieba(self):
        with patch.dict("sys.modules", {"jieba": None}):
            words = split_words("研究者公布新发现！", language="zh")

        self.assertEqual(words, ["研", "究", "者", "公", "布", "新", "发", "现"])

    def test_unsupported_language_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported language"):
            Summarize("Title", "Article text.", language="xx")

    def test_length_score_is_bounded(self):
        self.assertEqual(length_score(["word"] * 20), 1.0)
        self.assertEqual(length_score(["word"] * 40), 0.0)
        self.assertEqual(length_score(["word"] * 100), 0.0)

    def test_repeated_title_words_do_not_inflate_title_relevance(self):
        self.assertEqual(
            title_score(["government", "government"], ["government"] * 4),
            1.0,
        )

    def test_score_preserves_repeated_sentence_occurrences(self):
        repeated = "Repeated sentence."

        ranked = score([repeated, repeated], [], {})

        self.assertEqual([result[0] for result in ranked], [0, 1])
        self.assertEqual([result[1] for result in ranked], [repeated, repeated])


if __name__ == "__main__":
    unittest_main()
