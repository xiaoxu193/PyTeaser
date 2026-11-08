from pprint import pprint

from pyteaser import SummarizeUrl

urls = (
    "http://www.huffingtonpost.com/2013/11/22/twitter-forward-secrecy_n_4326599.html",
    "http://www.bbc.co.uk/news/world-europe-30035666",
    "http://www.bbc.co.uk/news/magazine-29631332",
)

for url in urls:
    summaries = SummarizeUrl(url)
    pprint(summaries)
