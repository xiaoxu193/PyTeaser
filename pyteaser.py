import argparse
from collections import Counter
from dataclasses import dataclass
from math import isfinite
import os
from pathlib import Path
from re import search as regex_search, sub as regex_sub, UNICODE as REGEX_UNICODE

stopWords = set([
    "-", " ", ",", ".", "a", "e", "i", "o", "u", "t", "about", "above",
    "across", "after", "afterwards", "again", "against", "all",
    "almost", "alone", "along", "already", "also", "although", "always",
    "am", "among", "amongst", "amoungst", "amount", "an", "and",
    "another", "any", "anyhow", "anyone", "anything", "anyway",
    "anywhere", "are", "around", "as", "at", "back", "be", "became",
    "because", "become", "becomes", "becoming", "been", "before",
    "beforehand", "behind", "being", "below", "beside", "besides",
    "between", "beyond", "both", "bottom", "but", "by", "call", "can",
    "cannot", "can't", "co", "con", "could", "couldn't", "de",
    "describe", "detail", "did", "do", "done", "down", "due", "during",
    "each", "eg", "eight", "either", "eleven", "else", "elsewhere",
    "empty", "enough", "etc", "even", "ever", "every", "everyone",
    "everything", "everywhere", "except", "few", "fifteen", "fifty",
    "fill", "find", "fire", "first", "five", "for", "former",
    "formerly", "forty", "found", "four", "from", "front", "full",
    "further", "get", "give", "go", "got", "had", "has", "hasnt",
    "have", "he", "hence", "her", "here", "hereafter", "hereby",
    "herein", "hereupon", "hers", "herself", "him", "himself", "his",
    "how", "however", "hundred", "i", "ie", "if", "in", "inc", "indeed",
    "into", "is", "it", "its", "it's", "itself", "just", "keep", "last",
    "latter", "latterly", "least", "less", "like", "ltd", "made", "make",
    "many", "may", "me", "meanwhile", "might", "mill", "mine", "more",
    "moreover", "most", "mostly", "move", "much", "must", "my", "myself",
    "name", "namely", "neither", "never", "nevertheless", "new", "next",
    "nine", "no", "nobody", "none", "noone", "nor", "not", "nothing",
    "now", "nowhere", "of", "off", "often", "on", "once", "one", "only",
    "onto", "or", "other", "others", "otherwise", "our", "ours",
    "ourselves", "out", "over", "own", "part", "people", "per",
    "perhaps", "please", "put", "rather", "re", "said", "same", "see",
    "seem", "seemed", "seeming", "seems", "several", "she", "should",
    "show", "side", "since", "sincere", "six", "sixty", "so", "some",
    "somehow", "someone", "something", "sometime", "sometimes",
    "somewhere", "still", "such", "take", "ten", "than", "that", "the",
    "their", "them", "themselves", "then", "thence", "there",
    "thereafter", "thereby", "therefore", "therein", "thereupon",
    "these", "they", "thickv", "thin", "third", "this", "those",
    "though", "three", "through", "throughout", "thru", "thus", "to",
    "together", "too", "top", "toward", "towards", "twelve", "twenty",
    "two", "un", "under", "until", "up", "upon", "us", "use", "very",
    "via", "want", "was", "we", "well", "were", "what", "whatever",
    "when", "whence", "whenever", "where", "whereafter", "whereas",
    "whereby", "wherein", "whereupon", "wherever", "whether", "which",
    "while", "whither", "who", "whoever", "whole", "whom", "whose",
    "why", "will", "with", "within", "without", "would", "yet", "you",
    "your", "yours", "yourself", "yourselves",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
    "sunday", "mon", "tue", "wed", "thu", "fri", "sat", "sun",
    "1", "10", "2012", "sa", "says", "pm",
    "2013", "na", "ng", "ang", "year", "years", "percent", "ko", "ako",
    "yung", "yun", "2", "3", "4", "5", "6", "7", "8", "9", "0", "time",
    "january", "february", "march", "april", "may", "june", "july",
    "august", "september", "october", "november", "december",
])
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
    "dr", "mr", "mrs", "ms", "prof", "rev", "sr", "jr", "st",
}
_NONTERMINAL_ABBREVIATIONS = {"e.g", "i.e", "n.b"}
_CONTEXTUAL_ABBREVIATIONS = {
    "a.m", "p.m", "u.s", "u.k", "u.n", "etc", "vs", "inc", "ltd",
    "corp", "co", "approx", "fig", "no", "vol", "jan", "feb", "mar",
    "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec",
}


@dataclass(frozen=True)
class ScoringWeights:
    """Non-negative weights for the summarizer's four sentence features."""

    title: float = TITLE_WEIGHT
    frequency: float = FREQUENCY_WEIGHT
    length: float = LENGTH_WEIGHT
    position: float = POSITION_WEIGHT

    def __post_init__(self):
        values = (self.title, self.frequency, self.length, self.position)
        if any(isinstance(value, bool) or not isinstance(value, (int, float))
               for value in values):
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


def SummarizeUrl(url, sentence_count=5, language=None, max_words=None,
                 weights=None):
    sentence_count = _validate_sentence_count(sentence_count)
    max_words = _validate_max_words(max_words)
    requested_language = (
        _normalize_language(language) if language is not None else None)
    url = _coerce_text(url, "url")
    if not url.strip():
        raise ValueError("url must not be empty")
    if sentence_count == 0 or max_words == 0:
        return []

    from lxml.etree import LxmlError
    from goose.network import FetchError

    try:
        article = grab_link(url)
    except FetchError as error:
        raise ArticleFetchError("Could not fetch the article URL") from error
    except (LxmlError, OSError, TypeError, ValueError) as error:
        raise ArticleExtractionError(
            "Could not extract an article from the URL") from error

    if not (article and article.cleaned_text and article.title):
        raise ArticleExtractionError(
            "The page did not contain both an article title and body text")

    if requested_language is None:
        try:
            requested_language = _normalize_language(article.meta_lang or "en")
        except ValueError:
            requested_language = "en"

    return Summarize(
        str(article.title),
        str(article.cleaned_text),
        sentence_count,
        language=requested_language,
        max_words=max_words,
        weights=weights,
    )


def Summarize(title, text, sentence_count=5, language="en", max_words=None,
              weights=None):
    """Return an extractive summary for a title and article text.

    Text arguments may be strings or UTF-8 encoded bytes. A missing title is
    treated as an empty string; blank article text produces an empty summary.
    ``language`` selects tokenization and bundled stopwords.
    """
    return [
        result.sentence
        for result in summarize_detailed(
            title, text, sentence_count, language, max_words, weights)
    ]


def summarize_detailed(title, text, sentence_count=5, language="en",
                       max_words=None, weights=None):
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
    keys = keywords(text, language, active_stop_words)
    titleWords = split_words(title, language)

    # Rank each occurrence separately, select the best sentences, then restore
    # the article's original order for a coherent extractive summary.
    ranked = sorted(
        score(
            sentences, titleWords, keys, language, active_stop_words,
            weights=weights),
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
    return [ScoredSentence(index, sentence, score)
            for index, sentence, score in selected]


def main(argv=None):
    """Command-line entry point for summarizing text, files, or URLs."""
    parser = argparse.ArgumentParser(description="Create an extractive summary")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url", help="article URL to fetch and summarize")
    source.add_argument("--text", help="article text to summarize")
    source.add_argument(
        "--input-file", type=Path, help="UTF-8 text file containing the article")
    parser.add_argument("--title", default=None, help="article title for text input")
    parser.add_argument("--sentence-count", type=int, default=5)
    parser.add_argument("--max-words", type=int, default=None)
    parser.add_argument("--language", default=None, help="language code such as en or es")
    args = parser.parse_args(argv)

    try:
        if args.url:
            summary = summarize_url(
                args.url,
                sentence_count=args.sentence_count,
                language=args.language,
                max_words=args.max_words,
            )
        else:
            text = args.text if args.text is not None else args.input_file.read_text(
                encoding="utf-8")
            summary = summarize(
                args.title,
                text,
                sentence_count=args.sentence_count,
                language=args.language or "en",
                max_words=args.max_words,
            )
    except (PyTeaserError, OSError, TypeError, ValueError) as error:
        parser.exit(2, "pyteaser: %s\n" % error)

    for sentence in summary:
        print(sentence)
    return 0


def summarize(title, text, sentence_count=5, language="en", max_words=None,
              weights=None):
    """PEP 8 spelling of :func:`Summarize`."""
    return Summarize(title, text, sentence_count, language, max_words, weights)


def summarize_url(url, sentence_count=5, language=None, max_words=None,
                  weights=None):
    """PEP 8 spelling of :func:`SummarizeUrl`."""
    return SummarizeUrl(url, sentence_count, language, max_words, weights)


def _coerce_text(value, name, allow_none=False):
    if value is None and allow_none:
        return ""
    if isinstance(value, bytes):
        try:
            value = value.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError("%s must contain valid UTF-8" % name) from error
    if not isinstance(value, str):
        raise TypeError("%s must be a string or UTF-8 bytes" % name)
    return value


def _normalize_language(language):
    if language is None:
        return "en"
    language = _coerce_text(language, "language")
    language = language.replace("_", "-").split("-", 1)[0].casefold()
    if language not in _SUPPORTED_LANGUAGES:
        raise ValueError("Unsupported language: %s" % language)
    return language


def _load_stop_words(language):
    language = _normalize_language(language)
    if language not in _STOP_WORDS_CACHE:
        path = os.path.join(
            os.path.dirname(__file__),
            "goose",
            "resources",
            "text",
            "stopwords-%s.txt" % language,
        )
        try:
            with open(path, "r", encoding="utf-8") as resource:
                _STOP_WORDS_CACHE[language] = {
                    line.strip().casefold()
                    for line in resource
                    if line.strip() and not line.lstrip().startswith("#")
                }
        except OSError as error:
            raise ValueError(
                "Stopword resource is missing for language: %s" % language
            ) from error
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
            raise TypeError("weights must define title, frequency, length, and position") from error
    if not isinstance(weights, ScoringWeights):
        raise TypeError("weights must be a ScoringWeights instance or a dict")
    return weights


def _select_non_redundant(
        ranked, sentence_count, threshold=0.8, language="en", stop_words=None,
        max_words=None):
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

        if (len(terms) >= 3 and any(
                len(existing) >= 3
                and _jaccard_similarity(terms, existing) >= threshold
                for existing in selected_terms)):
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
    #extract article information using Python Goose
    from goose import Goose
    return Goose().extract(url=inurl)


def score(sentences, titleWords, keywords, language="en", stop_words=None,
          weights=None):
    """Return ``(index, sentence, score)`` for every sentence occurrence."""
    if stop_words is None:
        stop_words = _load_stop_words(language)
    weights = _coerce_scoring_weights(weights)
    senSize = len(sentences)
    totalWeight = sum((
        weights.title, weights.frequency, weights.length, weights.position))
    ranks = []
    for i, s in enumerate(sentences):
        sentence = split_words(s, language)
        titleFeature = title_score(titleWords, sentence, stop_words)
        sentenceLength = length_score(sentence)
        sentencePosition = sentence_position(i+1, senSize)
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
    score = 0.0
    if len(words) == 0:
        return 0
    for word in words:
        if word in keywords:
            score += keywords[word]
    return (1.0 / abs(len(words)) * score)/10.0


def dbs(words, keywords):
    if (len(words) == 0):
        return 0

    summ = 0
    first = []
    second = []

    for i, word in enumerate(words):
        if word in keywords:
            score = keywords[word]
            if first == []:
                first = [i, score]
            else:
                second = first
                first = [i, score]
                dif = first[0] - second[0]
                summ += (first[1]*second[1]) / (dif ** 2)

    # number of intersections
    k = len(set(keywords.keys()).intersection(set(words))) + 1
    return (1/(k*(k+1.0))*summ)


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
    text = regex_sub(r'[^\w ]', '', text, flags=REGEX_UNICODE)  # strip special chars
    return [word.casefold() for word in text.split()]


def keywords(text, language="en", stop_words=None):
    """Get the top 10 keyword frequencies for text in the selected language.

    Stopwords are excluded before ranking.
    """
    language = _normalize_language(language)
    if stop_words is None:
        stop_words = _load_stop_words(language)
    text = split_words(text, language)
    numWords = len(text)  # of words before removing blacklist words
    freq = Counter(x for x in text if x not in stop_words)

    minSize = min(10, len(freq))  # get first 10
    top_keywords = dict(freq.most_common(minSize))

    for k in top_keywords:
        articleScore = top_keywords[k]*1.0 / numWords
        top_keywords[k] = articleScore * 1.5 + 1

    return top_keywords


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
            while (index < len(paragraph)
                   and paragraph[index] in _SENTENCE_PUNCTUATION):
                index += 1
            punctuation_end = index
            while (index < len(paragraph)
                   and paragraph[index] in _CLOSING_PUNCTUATION):
                index += 1

            punctuation = paragraph[punctuation_start:punctuation_end]
            at_end = index == len(paragraph)
            has_whitespace = not at_end and paragraph[index].isspace()
            no_space_boundary = any(
                mark in punctuation for mark in _NO_SPACE_SENTENCE_PUNCTUATION)
            if not (at_end or has_whitespace or no_space_boundary):
                continue

            if ("." in punctuation
                    and not no_space_boundary
                    and not _should_split_after_period(
                        paragraph, punctuation_start, index)):
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

    next_word = regex_search(
        r"\w+", text[boundary_end:], flags=REGEX_UNICODE)
    next_initial = next_word.group(0)[0] if next_word else ""
    if abbreviation in _CONTEXTUAL_ABBREVIATIONS:
        return not next_initial or next_initial.isupper()

    if (len(abbreviation) == 1 and abbreviation.isalpha()
            and next_initial.isupper()):
        return False
    return True



def length_score(sentence):
    return max(
        0.0,
        1.0 - abs(IDEAL_SENTENCE_LENGTH - len(sentence)) / IDEAL_SENTENCE_LENGTH,
    )


def title_score(title, sentence, stop_words=None):
    if stop_words is None:
        stop_words = stopWords
    title_terms = {word for word in title if word not in stop_words}
    if not title_terms:
        return 0.0

    sentence_terms = {word for word in sentence if word not in stop_words}
    return len(title_terms.intersection(sentence_terms)) / float(len(title_terms))


def sentence_position(i, size):
    """different sentence positions indicate different
    probability of being an important sentence"""

    normalized = i*1.0 / size
    if 0 < normalized <= 0.1:
        return 0.17
    elif 0.1 < normalized <= 0.2:
        return 0.23
    elif 0.2 < normalized <= 0.3:
        return 0.14
    elif 0.3 < normalized <= 0.4:
        return 0.08
    elif 0.4 < normalized <= 0.5:
        return 0.05
    elif 0.5 < normalized <= 0.6:
        return 0.04
    elif 0.6 < normalized <= 0.7:
        return 0.06
    elif 0.7 < normalized <= 0.8:
        return 0.04
    elif 0.8 < normalized <= 0.9:
        return 0.04
    elif 0.9 < normalized <= 1.0:
        return 0.15
    else:
        return 0
