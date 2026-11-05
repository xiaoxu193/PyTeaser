"""\

12-14-2013: Removed the StopWordsArabic class in order to remove nltk dependency for PyTeaser 

This is a python port of "Goose" originally licensed to Gravity.com
under one or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.

Python port was written by Xavier Grangier for Recrutae

Gravity.com licenses this file
to you under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import os
import re
import string
from goose.utils import FileHelper
from goose.utils.encoding import smart_unicode
TABSSPACE = re.compile(r'[\s\t]+')

def innerTrim(value):
    if isinstance(value, str):
        # remove tab and white space
        value = re.sub(TABSSPACE, ' ', value)
        value = ''.join(value.splitlines())
        return value.strip()
    return ''


def encodeValue(value):
    return smart_unicode(value, errors='replace')


class WordStats(object):

    def __init__(self):
        # total number of stopwords or
        # good words that we can calculate
        self.stop_word_count = 0

        # total number of words on a node
        self.word_count = 0

        # holds an actual list
        # of the stop words we found
        self.stop_words = []

    def get_stop_words(self):
        return self.stop_words

    def set_stop_words(self, words):
        self.stop_words = words

    def get_stopword_count(self):
        return self.stop_word_count

    def set_stopword_count(self, wordcount):
        self.stop_word_count = wordcount

    def get_word_count(self):
        return self.word_count

    def set_word_count(self, cnt):
        self.word_count = cnt


class StopWords(object):

    PUNCTUATION = re.compile(r"[^\w\s]", re.UNICODE)
    TRANS_TABLE = str.maketrans('', '', string.punctuation)
    _cached_stop_words = {}

    def __init__(self, language='en'):
        # TODO replace 'x' with class
        # to generate dynamic path for file to load
        if language not in self._cached_stop_words:
            path = os.path.join('text', 'stopwords-%s.txt' % language)
            self._cached_stop_words[language] = set(FileHelper.loadResourceFile(path).splitlines())
        self.STOP_WORDS = self._cached_stop_words[language]

    def remove_punctuation(self, content):
        if isinstance(content, bytes):
            content = content.decode('utf-8', 'replace')
        return self.PUNCTUATION.sub('', content)

    def candiate_words(self, stripped_input):
        return stripped_input.split(' ')

    def get_stopword_count(self, content):
        if not content:
            return WordStats()
        ws = WordStats()
        stripped_input = self.remove_punctuation(content)
        candiate_words = self.candiate_words(stripped_input)
        overlapping_stopwords = []
        c = 0
        for w in candiate_words:
            c += 1
            if w.lower() in self.STOP_WORDS:
                overlapping_stopwords.append(w.lower())

        ws.set_word_count(c)
        ws.set_stopword_count(len(overlapping_stopwords))
        ws.set_stop_words(overlapping_stopwords)
        return ws


class StopWordsChinese(StopWords):
    """
    Chinese segmentation
    """
    def __init__(self, language='zh'):
        # force zh language code
        super(StopWordsChinese, self).__init__(language='zh')

    def candiate_words(self, stripped_input):
        # jieba build a tree that takes sometime
        # avoid building the tree if we don't use
        # chinese language
        try:
            import jieba
        except ImportError:
            return [character for character in stripped_input if character.isalnum()]
        return jieba.cut(stripped_input, cut_all=True)


def stopwords_class_for_language(language, configured_class):
    """Choose Chinese segmentation automatically for the default analyzer."""
    if language == 'zh' and configured_class is StopWords:
        return StopWordsChinese
    return configured_class


class StopWordsArabic(StopWords):
    """
    Arabic segmentation
    """
    def __init__(self, language='ar'):
        # force ar language code
        super(StopWordsArabic, self).__init__(language='ar')

    def candiate_words(self, stripped_input):
        import nltk
        s = nltk.stem.isri.ISRIStemmer()
        words = []
        for word in nltk.tokenize.wordpunct_tokenize(stripped_input):
            words.append(s.stem(word))
        return words
