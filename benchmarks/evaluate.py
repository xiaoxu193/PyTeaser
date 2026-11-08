"""Run a small offline ROUGE-1 smoke benchmark for the extractive baseline."""

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


def main():
    scores = []
    for line in DATASET.read_text(encoding="utf-8").splitlines():
        example = json.loads(line)
        summary = summarize(example["title"], example["text"], sentence_count=2)
        scores.append(rouge_1_f1(example["reference"], " ".join(summary)))

    mean_score = sum(scores) / len(scores) if scores else 0.0
    print("examples=%d rouge1_f1=%.3f" % (len(scores), mean_score))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
