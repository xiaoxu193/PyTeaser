"""Run a small offline ROUGE smoke benchmark for the extractive baseline."""

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


def bigrams(sequence):
    return Counter(zip(sequence, sequence[1:], strict=False))


def _f1(overlap, reference_count, candidate_count):
    if not reference_count or not candidate_count or not overlap:
        return 0.0
    precision = overlap / candidate_count
    recall = overlap / reference_count
    return 2 * precision * recall / (precision + recall)


def rouge_1_f1(reference, candidate):
    reference_tokens = Counter(tokens(reference))
    candidate_tokens = Counter(tokens(candidate))
    overlap = sum((reference_tokens & candidate_tokens).values())
    return _f1(overlap, sum(reference_tokens.values()), sum(candidate_tokens.values()))


def rouge_2_f1(reference, candidate):
    reference_bigrams = bigrams(tokens(reference))
    candidate_bigrams = bigrams(tokens(candidate))
    overlap = sum((reference_bigrams & candidate_bigrams).values())
    return _f1(
        overlap, sum(reference_bigrams.values()), sum(candidate_bigrams.values())
    )


def longest_common_subsequence(reference, candidate):
    if not reference or not candidate:
        return 0
    previous = [0] * (len(candidate) + 1)
    for reference_token in reference:
        current = [0]
        for index, candidate_token in enumerate(candidate, start=1):
            if reference_token == candidate_token:
                current.append(previous[index - 1] + 1)
            else:
                current.append(max(current[index - 1], previous[index]))
        previous = current
    return previous[-1]


def rouge_l_f1(reference, candidate):
    reference_tokens = tokens(reference)
    candidate_tokens = tokens(candidate)
    overlap = longest_common_subsequence(reference_tokens, candidate_tokens)
    return _f1(overlap, len(reference_tokens), len(candidate_tokens))


METRICS = {
    "rouge1_f1": rouge_1_f1,
    "rouge2_f1": rouge_2_f1,
    "rougeL_f1": rouge_l_f1,
}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sentence-count", type=int, default=2)
    parser.add_argument(
        "--min-score",
        type=float,
        default=None,
        help="exit nonzero when the mean ROUGE-1 score falls below this threshold",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print per-example scores as JSON",
    )
    args = parser.parse_args(argv)

    per_example = []
    for line in DATASET.read_text(encoding="utf-8").splitlines():
        example = json.loads(line)
        summary = summarize(
            example["title"], example["text"], sentence_count=args.sentence_count
        )
        candidate = " ".join(summary)
        per_example.append(
            {
                "title": example["title"],
                **{
                    name: metric(example["reference"], candidate)
                    for name, metric in METRICS.items()
                },
            }
        )

    means = {
        name: (
            sum(example[name] for example in per_example) / len(per_example)
            if per_example
            else 0.0
        )
        for name in METRICS
    }
    print(
        f"examples={len(per_example)} "
        + " ".join(f"{name}={value:.3f}" for name, value in means.items())
    )

    if args.json:
        print(json.dumps({"means": means, "examples": per_example}, indent=2))

    if args.min_score is not None and means["rouge1_f1"] < args.min_score:
        print(
            f"mean ROUGE-1 F1 {means['rouge1_f1']:.3f} is below the "
            f"required {args.min_score:.3f}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
