# Offline quality smoke benchmark

Run from the repository root:

```bash
python benchmarks/evaluate.py
python benchmarks/evaluate.py --sentence-count 3 --min-score 0.30
```

The script reports mean unigram-overlap ROUGE-1 F1 for ten short,
hand-written examples written for this repository (no third-party corpus
licensing required). `--sentence-count` selects the summary length (default
2) and `--min-score` makes the run fail when quality regresses below a
threshold, which is useful in CI or pre-merge checks.

This is a deterministic regression signal only, not a representative
summarization benchmark. For model/algorithm comparisons, add a sufficiently
large, licensed corpus with independently authored references and report
standard metrics plus human review.
