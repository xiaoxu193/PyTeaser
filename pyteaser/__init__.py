"""Extractive summarization of article text and news URLs.

The public API is :func:`summarize` and :func:`summarize_url`, plus the
detailed variant :func:`summarize_detailed`. Sentences are ranked with a
weighted mix of title relevance, keyword frequency, length, and position;
near-duplicate sentences are filtered and results are returned in article
order. URL fetching and article extraction are provided by the bundled
Goose extractor.
"""

from __future__ import annotations

import argparse
import importlib.resources
import json
from bisect import bisect_left
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite, log
from pathlib import Path
from re import UNICODE as REGEX_UNICODE
from re import search as regex_search
from re import sub as regex_sub

__version__ = "2.0.0"


def _load_english_stop_words():
    """Load the historical PyTeaser English list shipped as package data."""
    resource = importlib.resources.files("pyteaser.resources").joinpath(
        "stopwords-en.txt"
    )
    return {
        line.strip().casefold()
        for line in resource.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


stopWords = _load_english_stop_words()
_SUPPORTED_LANGUAGES = {"ar", "de", "en", "es", "fr", "it", "ru", "sv", "zh"}
_STOP_WORDS_CACHE = {"en": stopWords}
# Sentence length (in words) that scores highest in the length feature.
IDEAL_SENTENCE_LENGTH = 20.0
TITLE_WEIGHT = 1.5
FREQUENCY_WEIGHT = 2.0
LENGTH_WEIGHT = 1.0
POSITION_WEIGHT = 1.0
_SENTENCE_PUNCTUATION = ".!?。！？؟।"
_CLOSING_PUNCTUATION = "\"'”’»)]}"
_NO_SPACE_SENTENCE_PUNCTUATION = "!?。！？؟।"
_TITLE_ABBREVIATIONS = {
    "dr",
    "mr",
    "mrs",
    "ms",
    "prof",
    "rev",
    "sr",
    "jr",
    "st",
}
_NONTERMINAL_ABBREVIATIONS = {"e.g", "i.e", "n.b"}
_CONTEXTUAL_ABBREVIATIONS = {
    "a.m",
    "p.m",
    "u.s",
    "u.k",
    "u.n",
    "etc",
    "vs",
    "inc",
    "ltd",
    "corp",
    "co",
    "approx",
    "fig",
    "no",
    "vol",
    "jan",
    "feb",
    "mar",
    "apr",
    "jun",
    "jul",
    "aug",
    "sep",
    "sept",
    "oct",
    "nov",
    "dec",
}


@dataclass(frozen=True)
class ScoringWeights:
    """Non-negative weights for the summarizer's four sentence features."""

    title: float = TITLE_WEIGHT
    frequency: float = FREQUENCY_WEIGHT
    length: float = LENGTH_WEIGHT
    position: float = POSITION_WEIGHT

    def __post_init__(self) -> None:
        values = (self.title, self.frequency, self.length, self.position)
        if any(
            isinstance(value, bool) or not isinstance(value, (int, float))
            for value in values
        ):
            raise TypeError("scoring weights must be numeric")
        if any(not isfinite(value) or value < 0 for value in values):
            raise ValueError("scoring weights must be finite and non-negative")
        if sum(values) == 0:
            raise ValueError("at least one scoring weight must be positive")


@dataclass(frozen=True)
class ScoredSentence:
    """A selected sentence and its source index and overall ranking score."""

    index: int
    sentence: str
    score: float


class PyTeaserError(Exception):
    """Base exception for URL article summarization failures."""


class ArticleFetchError(PyTeaserError):
    """Raised when an article page could not be fetched safely."""


class ArticleExtractionError(PyTeaserError):
    """Raised when a fetched page does not yield an article."""


def _fetch_article(
    url: str | bytes, language: str | None = None
) -> tuple[str, str, str]:
    """Fetch a URL and return its ``(title, text, language)`` triple."""
    url = _coerce_text(url, "url")
    if not url.strip():
        raise ValueError("url must not be empty")

    from lxml.etree import LxmlError

    from goose.network import FetchError

    try:
        article = grab_link(url)
    except FetchError as error:
        raise ArticleFetchError(f"Could not fetch the article URL: {error}") from error
    except (LxmlError, OSError, TypeError, ValueError) as error:
        raise ArticleExtractionError(
            f"Could not extract an article from the URL: {error}"
        ) from error

    if not (article and article.cleaned_text and article.title):
        raise ArticleExtractionError(
            "The page did not contain both an article title and body text"
        )

    if language is None:
        try:
            language = _normalize_language(article.meta_lang or "en")
        except ValueError:
            language = "en"
    return str(article.title), str(article.cleaned_text), language


def SummarizeUrl(
    url: str | bytes,
    sentence_count: int = 5,
    language: str | None = None,
    max_words: int | None = None,
    weights: ScoringWeights | dict[str, float] | None = None,
    keyword_scoring: str = "frequency",
) -> list[str]:
    sentence_count = _validate_sentence_count(sentence_count)
    max_words = _validate_max_words(max_words)
    requested_language = _normalize_language(language) if language is not None else None
    if sentence_count == 0 or max_words == 0:
        return []

    title, text, resolved_language = _fetch_article(url, requested_language)
    return Summarize(
        title,
        text,
        sentence_count,
        language=resolved_language,
        max_words=max_words,
        weights=weights,
        keyword_scoring=keyword_scoring,
    )


def Summarize(
    title: str | bytes | None,
    text: str | bytes,
    sentence_count: int = 5,
    language: str = "en",
    max_words: int | None = None,
    weights: ScoringWeights | dict[str, float] | None = None,
    keyword_scoring: str = "frequency",
) -> list[str]:
    """Return an extractive summary for a title and article text.

    Text arguments may be strings or UTF-8 encoded bytes. A missing title is
    treated as an empty string; blank article text produces an empty summary.
    ``language`` selects tokenization and bundled stopwords.
    """
    return [
        result.sentence
        for result in summarize_detailed(
            title, text, sentence_count, language, max_words, weights, keyword_scoring
        )
    ]


def summarize_detailed(
    title: str | bytes | None,
    text: str | bytes,
    sentence_count: int = 5,
    language: str = "en",
    max_words: int | None = None,
    weights: ScoringWeights | dict[str, float] | None = None,
    keyword_scoring: str = "frequency",
) -> list[ScoredSentence]:
    """Return selected sentences with their source indices and scores."""
    sentence_count = _validate_sentence_count(sentence_count)
    max_words = _validate_max_words(max_words)
    language = _normalize_language(language)
    active_stop_words = _load_stop_words(language)
    title = _coerce_text(title, "title", allow_none=True)
    text = _coerce_text(text, "text")
    if not text.strip():
        return []
    if sentence_count == 0 or max_words == 0:
        return []

    sentences = split_sentences(text)
    if not sentences:
        return []
    keys = keywords(text, language, active_stop_words, method=keyword_scoring)
    titleWords = split_words(title, language)

    # Rank each occurrence separately, select the best sentences, then restore
    # the article's original order for a coherent extractive summary.
    ranked = sorted(
        score(
            sentences, titleWords, keys, language, active_stop_words, weights=weights
        ),
        key=lambda result: (-result[2], result[0]),
    )
    selected = _select_non_redundant(
        ranked,
        sentence_count,
        language=language,
        stop_words=active_stop_words,
        max_words=max_words,
    )
    selected.sort(key=lambda result: result[0])
    return [
        ScoredSentence(index, sentence, score) for index, sentence, score in selected
    ]


def main(argv: Sequence[str] | None = None) -> int:
    """Command-line entry point for summarizing text, files, or URLs."""
    parser = argparse.ArgumentParser(
        description="Create an extractive summary",
        prog="pyteaser",
    )
    parser.add_argument(
        "--version", action="version", version="pyteaser " + __version__
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url", help="article URL to fetch and summarize")
    source.add_argument("--text", help="article text to summarize")
    source.add_argument(
        "--input-file", type=Path, help="UTF-8 text file containing the article"
    )
    parser.add_argument("--title", default=None, help="article title for text input")
    parser.add_argument("--sentence-count", type=int, default=5)
    parser.add_argument("--max-words", type=int, default=None)
    parser.add_argument(
        "--keyword-scoring",
        choices=("frequency", "tfidf"),
        default="frequency",
        help="keyword weighting used while ranking sentences",
    )
    parser.add_argument(
        "--language", default=None, help="language code such as en or es"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print selected sentences with indices and scores as JSON",
    )
    args = parser.parse_args(argv)

    if args.url and args.title is not None:
        parser.error("--title only applies to --text and --input-file input")

    try:
        if args.url:
            requested_language = (
                _normalize_language(args.language) if args.language else None
            )
            title, text, language = _fetch_article(args.url, requested_language)
        else:
            text = (
                args.text
                if args.text is not None
                else args.input_file.read_text(encoding="utf-8")
            )
            title = args.title
            language = args.language or "en"

        if args.json:
            results = summarize_detailed(
                title,
                text,
                sentence_count=args.sentence_count,
                language=language,
                max_words=args.max_words,
                keyword_scoring=args.keyword_scoring,
            )
            print(
                json.dumps(
                    [
                        {
                            "index": result.index,
                            "sentence": result.sentence,
                            "score": result.score,
                        }
                        for result in results
                    ],
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            summary = summarize(
                title,
                text,
                sentence_count=args.sentence_count,
                language=language,
                max_words=args.max_words,
                keyword_scoring=args.keyword_scoring,
            )
            for sentence in summary:
                print(sentence)
    except (PyTeaserError, OSError, TypeError, ValueError) as error:
        parser.exit(2, f"pyteaser: {error}\n")

    return 0


def summarize(
    title: str | bytes | None,
    text: str | bytes,
    sentence_count: int = 5,
    language: str = "en",
    max_words: int | None = None,
    weights: ScoringWeights | dict[str, float] | None = None,
    keyword_scoring: str = "frequency",
) -> list[str]:
    """PEP 8 spelling of :func:`Summarize`."""
    return Summarize(
        title, text, sentence_count, language, max_words, weights, keyword_scoring
    )


def summarize_url(
    url: str | bytes,
    sentence_count: int = 5,
    language: str | None = None,
    max_words: int | None = None,
    weights: ScoringWeights | dict[str, float] | None = None,
    keyword_scoring: str = "frequency",
) -> list[str]:
    """PEP 8 spelling of :func:`SummarizeUrl`."""
    return SummarizeUrl(
        url, sentence_count, language, max_words, weights, keyword_scoring
    )


def _coerce_text(value, name, allow_none=False):
    if value is None and allow_none:
        return ""
    if isinstance(value, bytes):
        try:
            value = value.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(f"{name} must contain valid UTF-8") from error
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string or UTF-8 bytes")
    return value


def _normalize_language(language):
    if language is None:
        return "en"
    language = _coerce_text(language, "language")
    language = language.replace("_", "-").split("-", 1)[0].casefold()
    if language not in _SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {language}")
    return language


def _load_stop_words(language):
    language = _normalize_language(language)
    if language not in _STOP_WORDS_CACHE:
        try:
            resource = importlib.resources.files("goose.resources.text").joinpath(
                f"stopwords-{language}.txt"
            )
            content = resource.read_text(encoding="utf-8")
        except (OSError, UnicodeError, ModuleNotFoundError) as error:
            raise ValueError(
                f"Stopword resource is missing for language: {language}"
            ) from error
        _STOP_WORDS_CACHE[language] = {
            line.strip().casefold()
            for line in content.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
    return _STOP_WORDS_CACHE[language]


def _validate_sentence_count(sentence_count):
    if isinstance(sentence_count, bool) or not isinstance(sentence_count, int):
        raise TypeError("sentence_count must be a non-negative integer")
    if sentence_count < 0:
        raise ValueError("sentence_count must be a non-negative integer")
    return sentence_count


def _validate_max_words(max_words):
    if max_words is None:
        return None
    if isinstance(max_words, bool) or not isinstance(max_words, int):
        raise TypeError("max_words must be a non-negative integer or None")
    if max_words < 0:
        raise ValueError("max_words must be a non-negative integer")
    return max_words


def _coerce_scoring_weights(weights):
    if weights is None:
        return ScoringWeights()
    if isinstance(weights, dict):
        try:
            return ScoringWeights(**weights)
        except TypeError as error:
            raise TypeError(
                "weights must define title, frequency, length, and position"
            ) from error
    if not isinstance(weights, ScoringWeights):
        raise TypeError("weights must be a ScoringWeights instance or a dict")
    return weights


def _select_non_redundant(
    ranked,
    sentence_count,
    threshold=0.8,
    language="en",
    stop_words=None,
    max_words=None,
):
    """Select high-ranked sentences while avoiding excessive word overlap."""
    if stop_words is None:
        stop_words = _load_stop_words(language)
    selected = []
    selected_terms = []
    selected_text = set()
    selected_word_count = 0
    for candidate in ranked:
        words = split_words(candidate[1], language)
        if max_words is not None and selected_word_count + len(words) > max_words:
            continue
        normalized_text = " ".join(words) or candidate[1].strip().casefold()
        if normalized_text in selected_text:
            continue

        terms = set(words)
        content_terms = terms.difference(stop_words)
        if content_terms:
            terms = content_terms

        if len(terms) >= 3 and any(
            len(existing) >= 3 and _jaccard_similarity(terms, existing) >= threshold
            for existing in selected_terms
        ):
            continue

        selected.append(candidate)
        selected_terms.append(terms)
        selected_text.add(normalized_text)
        selected_word_count += len(words)
        if len(selected) == sentence_count:
            break
    return selected


def _jaccard_similarity(left, right):
    union = left | right
    if not union:
        return 1.0
    return len(left & right) / float(len(union))


def grab_link(inurl):
    # extract article information using Python Goose
    from goose import Goose

    return Goose().extract(url=inurl)


def score(
    sentences, titleWords, keywords, language="en", stop_words=None, weights=None
):
    """Return ``(index, sentence, score)`` for every sentence occurrence."""
    if stop_words is None:
        stop_words = _load_stop_words(language)
    weights = _coerce_scoring_weights(weights)
    senSize = len(sentences)
    totalWeight = sum(
        (weights.title, weights.frequency, weights.length, weights.position)
    )
    ranks = []
    for i, s in enumerate(sentences):
        sentence = split_words(s, language)
        titleFeature = title_score(titleWords, sentence, stop_words)
        sentenceLength = length_score(sentence)
        sentencePosition = sentence_position(i + 1, senSize)
        sbsFeature = sbs(sentence, keywords)
        dbsFeature = dbs(sentence, keywords)
        frequency = (sbsFeature + dbsFeature) / 2.0 * 10.0

        totalScore = (
            titleFeature * weights.title
            + frequency * weights.frequency
            + sentenceLength * weights.length
            + sentencePosition * weights.position
        ) / totalWeight
        ranks.append((i, s, totalScore))
    return ranks


def sbs(words, keywords):
    """Score the share of sentence words that are top keywords."""
    score = 0.0
    if not words:
        return 0.0
    for word in words:
        if word in keywords:
            score += keywords[word]
    return (1.0 / abs(len(words)) * score) / 10.0


def dbs(words, keywords):
    """Score keyword density from products of adjacent keyword hits."""
    if not words:
        return 0.0

    total = 0.0
    previous = None  # (index, score) of the previous keyword hit

    for i, word in enumerate(words):
        if word in keywords:
            score = keywords[word]
            if previous is not None:
                distance = i - previous[0]
                total += (score * previous[1]) / (distance**2)
            previous = (i, score)

    # number of intersections
    k = len(set(keywords).intersection(words)) + 1
    return 1 / (k * (k + 1.0)) * total


def split_words(text, language="en"):
    """Tokenize text using the selected language's word boundary rules."""
    text = _coerce_text(text, "text")
    language = _normalize_language(language)
    if language == "zh":
        try:
            import jieba
        except ImportError:
            return [character.casefold() for character in text if character.isalnum()]
        return [
            token.casefold()
            for token in (
                regex_sub(r"[^\w]", "", word, flags=REGEX_UNICODE)
                for word in jieba.cut(text)
            )
            if token
        ]
    text = regex_sub(r"[^\w ]", "", text, flags=REGEX_UNICODE)  # strip special chars
    return [word.casefold() for word in text.split()]


_KEYWORD_METHODS = ("frequency", "tfidf")


def keywords(text, language="en", stop_words=None, method="frequency"):
    """Return up to ten keyword weights for text in the selected language.

    ``method="frequency"`` ranks words by their share of the article, the
    historical PyTeaser behavior. ``method="tfidf"`` additionally weights
    each word by how selectively it is spread across the article's
    sentences, downgrading words that appear everywhere. Stopwords are
    excluded before ranking in both cases.
    """
    language = _normalize_language(language)
    if method not in _KEYWORD_METHODS:
        raise ValueError(f"Unsupported keyword scoring method: {method}")
    if stop_words is None:
        stop_words = _load_stop_words(language)
    words = split_words(text, language)
    freq = Counter(word for word in words if word not in stop_words)
    if not freq:
        return {}

    if method == "tfidf":
        raw = _tfidf_keyword_weights(text, language, stop_words, words, freq)
    else:
        num_words = len(words)  # words before removing stopwords
        raw = dict(freq.most_common(10))
        raw = {term: count * 1.0 / num_words * 1.5 + 1 for term, count in raw.items()}
    return raw


def _tfidf_keyword_weights(text, language, stop_words, words, freq):
    """Weight terms by frequency times a sentence-level inverse document frequency."""
    documents = [
        {word for word in split_words(sentence, language) if word not in stop_words}
        for sentence in split_sentences(text)
    ]
    content_words = {word for word in words if word not in stop_words}
    documents = [document for document in documents if document] or [content_words]

    total = len(documents)
    weights = {}
    for term, count in freq.items():
        document_frequency = sum(1 for document in documents if term in document)
        idf = log((total + 1.0) / (document_frequency + 1.0)) + 1.0
        weights[term] = count * idf

    top = sorted(weights.items(), key=lambda item: item[1], reverse=True)[:10]
    max_weight = top[0][1] if top else 0.0
    if max_weight <= 0:
        return {}
    return {term: weight / max_weight * 1.5 + 1 for term, weight in top}


def split_sentences(text):
    """Split text into sentences while preserving punctuation and source order."""
    text = _coerce_text(text, "text")
    if not text.strip():
        return []

    sentences = []
    paragraphs = regex_sub(r"\n\s*\n+", "\n\n", text.strip()).split("\n\n")
    for paragraph in paragraphs:
        paragraph = regex_sub(r"\s+", " ", paragraph, flags=REGEX_UNICODE).strip()
        if not paragraph:
            continue

        start = 0
        index = 0
        while index < len(paragraph):
            if paragraph[index] not in _SENTENCE_PUNCTUATION:
                index += 1
                continue

            punctuation_start = index
            while index < len(paragraph) and paragraph[index] in _SENTENCE_PUNCTUATION:
                index += 1
            punctuation_end = index
            while index < len(paragraph) and paragraph[index] in _CLOSING_PUNCTUATION:
                index += 1

            punctuation = paragraph[punctuation_start:punctuation_end]
            at_end = index == len(paragraph)
            has_whitespace = not at_end and paragraph[index].isspace()
            no_space_boundary = any(
                mark in punctuation for mark in _NO_SPACE_SENTENCE_PUNCTUATION
            )
            if not (at_end or has_whitespace or no_space_boundary):
                continue

            if (
                "." in punctuation
                and not no_space_boundary
                and not _should_split_after_period(paragraph, punctuation_start, index)
            ):
                continue

            sentence = paragraph[start:index].strip()
            if sentence:
                sentences.append(sentence)
            start = index
            while start < len(paragraph) and paragraph[start].isspace():
                start += 1
            index = start

        trailing_text = paragraph[start:].strip()
        if trailing_text:
            sentences.append(trailing_text)

    return sentences


def _should_split_after_period(text, punctuation_start, boundary_end):
    match = regex_search(
        r"([^\W_]+(?:\.[^\W_]+)*)$",
        text[:punctuation_start],
        flags=REGEX_UNICODE,
    )
    if not match:
        return True

    abbreviation = match.group(1).casefold()
    if abbreviation in _TITLE_ABBREVIATIONS | _NONTERMINAL_ABBREVIATIONS:
        return False

    next_word = regex_search(r"\w+", text[boundary_end:], flags=REGEX_UNICODE)
    next_initial = next_word.group(0)[0] if next_word else ""
    if abbreviation in _CONTEXTUAL_ABBREVIATIONS:
        return not next_initial or next_initial.isupper()

    return not (
        len(abbreviation) == 1 and abbreviation.isalpha() and next_initial.isupper()
    )


def length_score(sentence):
    return max(
        0.0,
        1.0 - abs(IDEAL_SENTENCE_LENGTH - len(sentence)) / IDEAL_SENTENCE_LENGTH,
    )


def title_score(title, sentence, stop_words=None):
    if stop_words is None:
        stop_words = _load_stop_words("en")
    title_terms = {word for word in title if word not in stop_words}
    if not title_terms:
        return 0.0

    sentence_terms = {word for word in sentence if word not in stop_words}
    return len(title_terms.intersection(sentence_terms)) / float(len(title_terms))


_POSITION_BOUNDARIES = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
_POSITION_SCORES = (0.17, 0.23, 0.14, 0.08, 0.05, 0.04, 0.06, 0.04, 0.04, 0.15)


def sentence_position(i, size):
    """Score a sentence by its relative position in the article.

    Lead sentences (and, more weakly, closing ones) are more likely to be
    central, mirroring the original Graph-Based Sentence ranker.
    """
    normalized = i * 1.0 / size
    if not 0 < normalized <= 1.0:
        return 0.0
    return _POSITION_SCORES[bisect_left(_POSITION_BOUNDARIES, normalized)]
