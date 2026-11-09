"""Quick demonstration of the PyTeaser API.

Run without arguments for an offline example, or pass news URLs to fetch
and summarize them:

    python demo.py
    python demo.py https://example.com/news/article
"""

import sys

from pyteaser import SummarizeUrl, summarize


def demo_offline():
    title = "A sample article"
    text = (
        "Researchers announced a compact method for summarizing news articles. "
        "The approach ranks sentences by title relevance, keyword frequency, "
        "length, and position. Sentences that repeat existing content are "
        "filtered out of the final summary. The remaining sentences keep their "
        "original order so the summary reads naturally. Early results were "
        "presented at a small workshop last month."
    )
    for sentence in summarize(title, text, sentence_count=2):
        print(sentence)


def demo_urls(urls):
    for url in urls:
        print(url)
        try:
            summaries = SummarizeUrl(url)
        except Exception as error:  # demo: show any failure and move on
            print(f"  failed: {error}")
            continue
        for sentence in summaries:
            print(f"  {sentence}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        demo_urls(sys.argv[1:])
    else:
        demo_offline()
