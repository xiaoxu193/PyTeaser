# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `pyteaser.__version__` and a `--version` command-line flag.
- `--json` CLI output with each sentence's original index and score.
- The CLI can now be run as `python -m pyteaser`.
- Benchmark script options: `--sentence-count` and a `--min-score` gate.
- Contributing guide, security policy, changelog, issue/PR templates,
  Dependabot, pre-commit config, release workflow, coverage reporting, and
  formatting checks in CI.
- Opt-in TF-IDF keyword scoring (`keyword_scoring="tfidf"`,
  `--keyword-scoring tfidf`) that discounts words spread across every
  sentence.
- Opt-in maximal-marginal-relevance sentence selection
  (`selection="mmr"`, `--selection mmr --mmr-lambda 0.7`).
- Language-aware ideal sentence lengths for the length feature (about 30
  tokens for Chinese character tokenization).
- Benchmark corpus expanded to ten examples and now reports ROUGE-1,
  ROUGE-2, and ROUGE-L with `--json` detail.
- mypy type checking (the package now ships `py.typed`).

### Changed

- Packaging metadata migrated from `setup.py` to PEP 621 `pyproject.toml`;
  the version now comes from `pyteaser.__version__`.
- The single-module layout became a `pyteaser/` package so typed consumers
  get inline type information.
- The default English stopword list now ships as package data instead of an
  inline literal (a bare-space entry that tokenization can never produce was
  dropped).
- Destination port policy is configurable (`allowed_ports`) and independent
  of `allow_private_network`, which now only controls host reachability.
- The test suite moved from `tests.py` to a `tests/` package.
- URL fetch and extraction errors now include the underlying reason.
- The demo script runs offline by default and accepts optional URLs.
- Vendored Goose code modernized (old-style classes, `super()` calls,
  Python 2 coding declarations, typo fixes, dead code removal).
- GitHub Actions are pinned to commit SHAs.

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
