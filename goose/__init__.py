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
from goose.version import __version__ as __version__
from goose.version import version_info as version_info
from goose.configuration import Configuration
from goose.crawler import CrawlCandidate
from goose.crawler import Crawler


class Goose:
    """\

    """

    def __init__(self, config=None):
        self.config = config or Configuration()
        self.extend_config()
        self.initialize()

    def extend_config(self):
        if isinstance(self.config, dict):
            config = Configuration()
            for k, v in self.config.items():
                if hasattr(config, k):
                    setattr(config, k, v)
            self.config = config

    def extract(self, url=None, raw_html=None):
        """\
        Main method to extract an article object from a URL,
        pass in a url and get back a Article
        """
        cc = CrawlCandidate(self.config, url, raw_html)
        return self.crawl(cc)

    def shutdown_network(self):
        pass

    def crawl(self, crawl_candiate):
        crawler = Crawler(self.config)
        article = crawler.crawl(crawl_candiate)
        return article

    def initialize(self):
        storage_path = self.config.local_storage_path
        try:
            os.makedirs(storage_path, exist_ok=True)
        except OSError as error:
            raise OSError(
                storage_path + " directory does not seem to exist, "
                "you need to set this for image processing downloads"
            ) from error

        if not os.path.isdir(storage_path):
            raise OSError(
                storage_path + " directory does not seem to exist, "
                "you need to set this for image processing downloads"
            )

        try:
            with tempfile.NamedTemporaryFile(
                prefix=".goose-write-test-", dir=storage_path, delete=True
            ):
                pass
        except OSError as error:
            raise OSError(
                storage_path + " directory is not writable, "
                "you need to set this for image processing downloads"
            ) from error
