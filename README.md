PyTeaser
========

PyTeaser is based on the original [TextTeaser](https://github.com/MojoJolo/textteaser) project written in Scala by Mojojolo. It's completely re-written in Python.

The aim of PyTeaser is is to take any news article and extract a brief summary from it.


# Requirements:

Install [nltk](http://nltk.org/install.html) to split sentences.

(Optional) Install [Python-Goose](https://github.com/grangier/python-goose) to extract text and other meta information
from an url (Only if you want to use SummarizeUrl).





# Use:
## sample command:
```Python
>>> from pyteaser import SummarizeUrl
>>> url = 'http://www.huffingtonpost.com/2013/11/22/twitter-forward-secrecy_n_4326599.html'
>>> summaries = SummarizeUrl(url)
>>> print summaries

```

## output
```
[
  'Twitter\'s move is the latest response from U.S. Internet firms following disclosures by former spy agency contractor Edward Snowden about widespread, classified U.S. government surveillance programs.', 
  'Since then, it has become clearer and clearer how important that step was to protecting our users\' privacy.', 
  'The online messaging service, which began scrambling communications in 2011 using traditional HTTPS encryption, said on Friday it has added an advanced layer of protection for HTTPS known as "forward secrecy.', 
  '"A year and a half ago, Twitter was first served completely over HTTPS," the company said in a blog posting.', 
  'By Jim Finkle (Reuters) - Twitter Inc said it has implemented a security technology that makes it harder to spy on its users and called on other Internet firms to do the same, as Web providers look to thwart spying by government intelligence agencies.'
]

```

you can use Summarize(title, text) directly if you have those available already. Otherwise you must install Python Goose to extract text from url.


#todo:
- Remove dependency on Python nltk because it's annoying to install