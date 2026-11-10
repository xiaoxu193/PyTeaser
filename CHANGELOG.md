# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `pyteaser.__version__` and a `--version` command-line flag.
- `--json` CLI output with each sentence's original index and score.
- The CLI can now be run as `python -m pyteaser` or `python pyteaser.py`.
- Benchmark script options: `--sentence-count` and a `--min-score` gate.
- Contributing guide, security policy, changelog, issue/PR templates,
  Dependabot, pre-commit config, release workflow, coverage reporting, and
  formatting checks in CI.

### Changed

- Packaging metadata migrated from `setup.py` to PEP 621 `pyproject.toml`;
  the version now comes from `pyteaser.__version__`.
- The test suite moved from `tests.py` to a `tests/` package.
- URL fetch and extraction errors now include the underlying reason.
- The demo script runs offline by default and accepts optional URLs.
- Vendored Goose code modernized (old-style classes, `super()` calls,
  Python 2 coding declarations, typo fixes, dead code removal).

### Fixed

- `--title` is now rejected when combined with `--url` instead of being
  silently ignored.
- The Goose HTML parser no longer stores parsed documents as shared class
  state.

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
