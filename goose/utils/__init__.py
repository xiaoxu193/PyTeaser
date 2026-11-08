"""\
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

import hashlib
import os
import re
import time
import urllib.parse as urlparse

import goose


class BuildURL:
    def __init__(self, url, finalurl=None):
        self.url = url
        self.finalurl = finalurl

    def getHostname(self, o):
        if o.hostname:
            return o.hostname
        elif self.finalurl:
            oo = urlparse.urlparse(self.finalurl)
            if oo.hostname:
                return oo.hostname
        return None

    def getScheme(self, o):
        if o.scheme:
            return o.scheme
        elif self.finalurl:
            oo = urlparse.urlparse(self.finalurl)
            if oo.scheme:
                return oo.scheme
        return "http"

    def getUrl(self):
        """\

        """
        candidate = (
            urlparse.urljoin(self.finalurl, self.url) if self.finalurl else self.url
        )
        url_obj = urlparse.urlparse(candidate)
        scheme = self.getScheme(url_obj)
        hostname = self.getHostname(url_obj)
        if not hostname:
            return None

        netloc = url_obj.netloc or hostname
        if not url_obj.netloc and url_obj.port:
            netloc = f"{hostname}:{url_obj.port}"
        return urlparse.urlunparse(
            (
                scheme,
                netloc,
                url_obj.path,
                url_obj.params,
                url_obj.query,
                url_obj.fragment,
            )
        )


class FileHelper:
    @classmethod
    def loadResourceFile(cls, filename):
        if not os.path.isabs(filename):
            dirpath = os.path.dirname(goose.__file__)
            path = os.path.join(dirpath, "resources", filename)
        else:
            path = filename
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
            return content
        except OSError:
            raise OSError(f"Couldn't open file {path}")


class ParsingCandidate:
    def __init__(self, urlString, link_hash):
        self.urlString = self.url = urlString
        self.link_hash = link_hash


class RawHelper:
    @classmethod
    def get_parsing_candidate(cls, url, raw_html):
        if isinstance(raw_html, str):
            raw_html = raw_html.encode("utf-8")
        link_hash = f"{hashlib.md5(raw_html).hexdigest()}.{time.time()}"
        return ParsingCandidate(url, link_hash)


class URLHelper:
    @classmethod
    def get_parsing_candidate(cls, url_to_crawl):
        # replace shebang is urls
        final_url = (
            url_to_crawl.replace("#!", "?_escaped_fragment_=")
            if "#!" in url_to_crawl
            else url_to_crawl
        )
        link_hash = "{}.{}".format(
            hashlib.md5(final_url.encode("utf-8")).hexdigest(),
            time.time(),
        )
        return ParsingCandidate(final_url, link_hash)


class StringSplitter:
    """\

    """

    def __init__(self, pattern):
        self.pattern = re.compile(pattern)

    def split(self, string):
        if not string:
            return []
        return self.pattern.split(string)


class StringReplacement:
    def __init__(self, pattern, replaceWith):
        self.pattern = pattern
        self.replaceWith = replaceWith

    def replaceAll(self, string):
        if not string:
            return ""
        return string.replace(self.pattern, self.replaceWith)


class ReplaceSequence:
    def __init__(self):
        self.replacements = []

    # @classmethod
    def create(self, firstPattern, replaceWith=None):
        result = StringReplacement(firstPattern, replaceWith or "")
        self.replacements.append(result)
        return self

    def append(self, pattern, replaceWith=None):
        return self.create(pattern, replaceWith)

    def replaceAll(self, string):
        if not string:
            return ""

        mutatedString = string

        for rp in self.replacements:
            mutatedString = rp.replaceAll(mutatedString)
        return mutatedString
