# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0]

### Added

- PEP 8 `summarize` and `summarize_url` APIs alongside the legacy `Summarize` and
  `SummarizeUrl` names.
- `summarize_detailed` returning each selected sentence's source index and score.
- Configurable sentence scoring weights via `ScoringWeights`.
- Optional `max_words` summary budget.
- `pyteaser` command-line interface for text, file, and URL input.
- Bundled stopword resources for English, Spanish, Italian, German, Swedish,
  Russian, French, Arabic, and Chinese (jieba-backed segmentation when installed).
- Hardened URL fetching: HTTP(S)-only, request timeouts, response size limits,
  redirect revalidation, and private-network blocking by default.
- Publication-date and Open Graph/JSON-LD title fallbacks in article extraction.
- Offline test suite, ROUGE-1 smoke benchmark, Ruff linting, and GitHub Actions CI.

### Changed

- Image extraction is disabled by default and now requires the `images` extra
  (Pillow).
- Python 3.10 or newer is required.

## [1.0.0]

- Initial PyTeaser release with `Summarize` and `SummarizeUrl`.
