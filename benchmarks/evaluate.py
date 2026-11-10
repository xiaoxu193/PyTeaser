"""Run a small offline ROUGE-1 smoke benchmark for the extractive baseline."""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pyteaser import summarize  # noqa: E402

TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)
DATASET = Path(__file__).with_name("articles.jsonl")


def tokens(text):
    return [token.casefold() for token in TOKEN_PATTERN.findall(text)]


def rouge_1_f1(reference, candidate):
    reference_tokens = Counter(tokens(reference))
    candidate_tokens = Counter(tokens(candidate))
    overlap = sum((reference_tokens & candidate_tokens).values())
    if not reference_tokens or not candidate_tokens or not overlap:
        return 0.0
    precision = overlap / sum(candidate_tokens.values())
    recall = overlap / sum(reference_tokens.values())
    return 2 * precision * recall / (precision + recall)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sentence-count", type=int, default=2)
    parser.add_argument(
        "--min-score",
        type=float,
        default=None,
        help="exit nonzero when the mean score falls below this threshold",
    )
    args = parser.parse_args(argv)

    scores = []
    for line in DATASET.read_text(encoding="utf-8").splitlines():
        example = json.loads(line)
        summary = summarize(
            example["title"], example["text"], sentence_count=args.sentence_count
        )
        scores.append(rouge_1_f1(example["reference"], " ".join(summary)))

    mean_score = sum(scores) / len(scores) if scores else 0.0
    print(f"examples={len(scores)} rouge1_f1={mean_score:.3f}")

    if args.min_score is not None and mean_score < args.min_score:
        print(
            f"mean ROUGE-1 F1 {mean_score:.3f} is below the "
            f"required {args.min_score:.3f}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
