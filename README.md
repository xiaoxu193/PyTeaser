# PyTeaser

[![CI](https://github.com/xiaoxu193/PyTeaser/actions/workflows/ci.yml/badge.svg)](https://github.com/xiaoxu193/PyTeaser/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/pyteaser.svg)](https://pypi.org/project/pyteaser/)
[![Python versions](https://img.shields.io/pypi/pyversions/pyteaser.svg)](https://pypi.org/project/pyteaser/)
[![License](https://img.shields.io/pypi/l/pyteaser.svg)](LICENSE)

PyTeaser extracts a short, extractive summary from article text or a news URL. It ranks sentences using title relevance, article keywords, sentence length, and position, then removes repeated content and returns the selected sentences in the article's original order.

## Requirements and installation

PyTeaser requires Python 3.10 or newer.

```bash
python -m pip install pyteaser
```

Optional functionality is installed separately:

```bash
python -m pip install 'pyteaser[images]'   # Pillow-backed image extraction
python -m pip install 'pyteaser[chinese]'   # jieba Chinese word segmentation
python -m pip install 'pyteaser[soup]'      # BeautifulSoup-based fallback parser
python -m pip install 'pyteaser[all]'       # all optional features
```

When working from a source checkout, replace `pyteaser` with `.` (or `.[all]`).

## Summarize text

```python
from pyteaser import summarize

title = "A sample article"
text = "The first sentence explains the announcement. A second sentence gives context. A third sentence describes what happens next."

summary = summarize(title, text, sentence_count=2, language="en")
for sentence in summary:
    print(sentence)
```

`title` may be `None`; article text must be a string or UTF-8 bytes. Blank text returns an empty list. `sentence_count` defaults to 5, must be a non-negative integer, and may be set to 0 to request no sentences. Optional `max_words` sets a total token budget; candidates that do not fit are skipped.

Scoring weights default to title `1.5`, keyword frequency `2.0`, length `1.0`, and position `1.0`. Pass a `ScoringWeights` instance or a dictionary with those feature names to tune the heuristic.

By default keywords are ranked by their share of the article. Pass `keyword_scoring="tfidf"` to weight words by how selectively they spread across the article's sentences, which downgrades boilerplate that appears everywhere. The CLI exposes the same choice as `--keyword-scoring {frequency,tfidf}`.

For score inspection, `summarize_detailed(...)` returns records with each selected sentence's original `index`, text in `sentence`, and overall `score`. The normal APIs continue to return plain strings.

## Command line

After installation, summarize text or a UTF-8 file:

```bash
pyteaser --title "Example article" --text "First sentence. Second sentence." --sentence-count 1
pyteaser --input-file article.txt --title "Example article" --max-words 120
pyteaser --url "https://example.com/news/article" --sentence-count 3
pyteaser --title "Example article" --text "First sentence. Second sentence." --json
pyteaser --version
```

`--json` prints one record per selected sentence with its original `index`, `sentence` text, and `score`.

The original `Summarize(title, text)` function remains available. Both APIs return a list of sentence strings.

## Summarize a URL

```python
from pyteaser import summarize_url

summary = summarize_url("https://example.com/news/article", sentence_count=3)
```

URL summarization extracts the page's title and article text first. If the page declares a supported language, PyTeaser uses its stopword list; otherwise English is used. You can also explicitly pass `language="es"`, for example.

The bundled language resources cover English, Spanish, Italian, German, Swedish, Russian, French, Arabic, and Chinese. Chinese segmentation uses jieba when installed; without it, PyTeaser falls back to character tokenization. Language support is heuristic, so review summaries for your content and audience.

The legacy `SummarizeUrl(url)` function remains available. URL summarization returns a list, or raises `ArticleFetchError` when a page cannot be fetched safely and `ArticleExtractionError` when no title/body can be extracted. Invalid text, language, and sentence-count inputs raise `TypeError` or `ValueError`.

## URL and image safety

URL fetching accepts HTTP(S), applies a 10-second request timeout and a 5 MiB HTML limit, validates resolved addresses and redirect targets, blocks private/non-routable addresses by default, and restricts destination ports to 80/443 (configurable via Goose's `allowed_ports`, or `None` to disable) independently of the private-network setting. Image fetching is disabled by default; enable it only when needed:

```python
from goose import Goose

article = Goose({"enable_image_fetching": True}).extract(
    url="https://example.com/news/article"
)
print(article.top_image.src)
```

Image downloads are capped at 15 MiB and require the `images` extra. Applications processing untrusted URLs should keep private-network access disabled. For trusted local development only, Goose supports `allow_private_network=True`; do not enable this for user-controlled URLs.

Use article extraction responsibly and comply with the target site's terms and applicable law.

## Tests

The test suite is offline; URL cases use mocked responses or a local loopback server.

```bash
python -m pip install -e '.[all,dev]'
python -m unittest discover -v
ruff check .
ruff format --check .
python benchmarks/evaluate.py
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, pull request guidelines, and
[CHANGELOG.md](CHANGELOG.md) for release history. Security reports follow the
policy in [SECURITY.md](SECURITY.md).

## License

PyTeaser's original code is MIT-licensed. The bundled Goose article extractor and its included resources are Apache-2.0-licensed; see `LICENSE`, `goose/LICENSE.txt`, and `NOTICE` for license and attribution details.
