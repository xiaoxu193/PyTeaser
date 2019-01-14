PyTeaser
========

PyTeaser is a Python 3 library that takes any English news article and extracts a brief summary from it. It's based on the original [Scala](https://github.com/MojoJolo/textteaser) project.

```python
>>> from pyteaser import SummarizeUrl
>>> url = 'http://www.huffingtonpost.com/2013/11/22/twitter-forward-secrecy_n_4326599.html'
>>> summary = SummarizeUrl(url)
>>> print(summary)
['"A year and a half ago, Twitter was first served completely over HTTPS," the company said in a blog posting.', 
'(Reuters) - Twitter Inc said it has implemented a security technology that makes it harder to spy on its users and called on other Internet firms to do the same, as Web providers look to thwart spying by government intelligence agencies.', 
"Twitter's move is the latest response from U.S. Internet firms following disclosures by former spy agency contractor Edward Snowden about widespread, classified U.S. government surveillance programs.", 
'"Since then, it has become clearer and clearer how important that step was to protecting our users\' privacy."', 
'Facebook Inc, Google Inc, Microsoft Corp and Yahoo Inc have publicly complained that the government does not let them disclose data collection efforts.']
```

Summaries are created by ranking sentences in a news article according to how relevant they are to the entire text. The top 5 sentences are used to form a "summary". Each sentence is ranked by using four criteria:

- Relevance to the title
- Relevance to keywords in the article
- Position of the sentence
- Length of the sentence


### Installation

```
pip install pyteaser
```


PyTeaser relies on [goose3](https://github.com/goose3/goose3) for extracting the article body and title from webpages. You can also use `Summarize(title, text)` directly if you already have the title and article text (both should be strings). 
