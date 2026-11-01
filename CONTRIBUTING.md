# Contributing to PyTeaser

Thanks for your interest in improving PyTeaser! Bug reports, fixes, docs, and
tests are all welcome.

## Getting set up

```bash
git clone https://github.com/xiaoxu193/PyTeaser.git
cd PyTeaser
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[all,dev]'
```

## Running the checks

The test suite is fully offline; URL cases use mocked responses or a loopback
server.

```bash
python -m unittest discover -v   # tests
ruff check .                     # lint
ruff format --check .            # formatting
python benchmarks/evaluate.py    # summarization smoke benchmark
```

Please run all four before opening a pull request, and add tests for any
behavior change. Fixes should keep the benchmark from regressing.

## Pull request guidelines

- One logical change per pull request, with a focused description.
- Keep the public API documented in `README.md` up to date.
- New network behavior must respect the URL safety rules described in the
  README (scheme allow-list, timeouts, size limits, private-network blocking).
- Note user-visible changes in `CHANGELOG.md`.

## Reporting bugs

Include the PyTeaser version, Python version, a minimal reproduction, and — for
extraction issues — a saved copy of the HTML whenever possible.

## Licensing

By contributing, you agree that your contributions will be dual-licensed under
the repository's MIT (original PyTeaser code) and Apache-2.0 (bundled Goose
code and resources) terms; see `LICENSE`, `goose/LICENSE.txt`, and `NOTICE`.
