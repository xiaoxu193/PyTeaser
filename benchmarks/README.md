# Offline quality smoke benchmark

Run from the repository root:

```bash
python benchmarks/evaluate.py
python benchmarks/evaluate.py --sentence-count 3 --min-score 0.30
python benchmarks/evaluate.py --json
```

The script reports mean ROUGE-1, ROUGE-2 (bigram), and ROUGE-L (longest
common subsequence) F1 for ten short, hand-written examples written for this
repository (no third-party corpus licensing required). `--sentence-count`
selects the summary length (default 2), `--min-score` makes the run fail
when ROUGE-1 quality regresses below a threshold, and `--json` prints
per-example detail.

This is a deterministic regression signal only, not a representative
summarization benchmark. For model/algorithm comparisons, add a sufficiently
large, licensed corpus with independently authored references and report
standard metrics plus human review.
