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

import os
import tempfile

from goose.parsers import Parser, ParserSoup
from goose.text import StopWords
from goose.version import __version__


class Configuration:
    def __init__(self):
        # What's the minimum bytes for an image we'd accept is,
        # alot of times we want to filter out the author's little images
        # in the beginning of the article
        self.images_min_bytes = 4500

        # Image extraction is optional and disabled by default. Enable it
        # explicitly when the caller needs article images.
        self.enable_image_fetching = False

        # set this variable to False if you want to force
        # the article language. Otherwise it will attempt to
        # find meta language and use the correct stopwords dictionary
        self.use_meta_language = True

        # default language
        # it will be use as fallback
        # if use_meta_language is set to false, targetlanguage will
        # be use
        self.target_language = "en"

        # default stopwords class
        self.stopwords_class = StopWords

        # used as the user agent that
        # is sent with your web requests to extract an article
        # self.browser_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2)"\
        #                         " AppleWebKit/534.52.7 (KHTML, like Gecko) "\
        #                         "Version/5.1.2 Safari/534.52.7"
        self.browser_user_agent = f"Goose/{__version__}"

        # Network safety and resource limits for article/image downloads.
        self.request_timeout = 10.0
        self.max_html_bytes = 5 * 1024 * 1024
        self.max_image_bytes = 15 * 1024 * 1024
        self.allow_private_network = False

        # debug mode
        # enable this to have additional debugging information
        # sent to stdout
        self.debug = False

        # Optional hook overriding the extracted publish date
        # (a concrete PublishDateExtractor instance).
        self.extract_publishdate = None

        # Optional hook for extra site-specific data
        # (a concrete AdditionalDataExtractor instance).
        self.additional_data_extractor = None

        # Parser type
        self.parser_class = "lxml"

    @property
    def local_storage_path(self):
        return os.path.join(tempfile.gettempdir(), "goose")

    def get_parser(self):
        return Parser if self.parser_class == "lxml" else ParserSoup

    def get_publishdate_extractor(self):
        return self.extract_publishdate

    def set_publishdate_extractor(self, extractor):
        """\
        Pass in to extract article publish dates.
        @param extractor a concrete instance of PublishDateExtractor
        """
        if not extractor:
            raise ValueError("extractor must not be null!")
        self.extract_publishdate = extractor

    def get_additionaldata_extractor(self):
        return self.additional_data_extractor

    def set_additionaldata_extractor(self, extractor):
        """\
        Pass in to extract any additional data not defined within
        @param extractor a concrete instance of AdditionalDataExtractor
        """
        if not extractor:
            raise ValueError("extractor must not be null!")
        self.additional_data_extractor = extractor
