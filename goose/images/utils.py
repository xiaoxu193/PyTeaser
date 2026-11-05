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
import warnings
from http.client import HTTPException
from urllib.error import HTTPError, URLError

from goose.network import fetch_bytes
from goose.utils.encoding import smart_str
from goose.images.image import ImageDetails
from goose.images.image import LocallyStoredImage


class ImageUtils(object):

    @classmethod
    def get_image_dimensions(self, identify_program, path):
        try:
            from PIL import Image
        except ImportError as error:
            raise RuntimeError(
                "Image extraction requires Pillow; install pyteaser[images]."
            ) from error

        image_details = ImageDetails()
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(path) as image:
                    image_details.set_mime_type(image.format)
                    width, height = image.size
        except (
            Image.DecompressionBombError,
            Image.DecompressionBombWarning,
            OSError,
            ValueError,
        ) as error:
            raise ValueError("Invalid or unsafe image data") from error
        image_details.set_width(width)
        image_details.set_height(height)
        return image_details

    @classmethod
    def store_image(self, http_client, link_hash, src, config):
        """\
        Writes an image src http string to disk as a temporary file
        and returns the LocallyStoredImage object
        that has the info you should need on the image
        """
        # check for a cache hit already on disk
        image = self.read_localfile(link_hash, src, config)
        if image:
            return image

        # no cache found download the image
        data = self.fetch(http_client, src, config)
        if data:
            image = self.write_localfile(data, link_hash, src, config)
            if image:
                return image

        return None

    @classmethod
    def get_mime_type(self, image_details):
        mime_type = (image_details.get_mime_type() or '').lower()
        mimes = {
            'png': '.png',
            'jpg': '.jpg',
            'jpeg': '.jpg',
            'gif': '.gif',
            'webp': '.webp',
            'bmp': '.bmp',
            'tiff': '.tiff',
        }
        return mimes.get(mime_type, 'NA')

    @classmethod
    def read_localfile(self, link_hash, src, config):
        local_image_name = self.get_localfile_name(link_hash, src, config)
        if os.path.isfile(local_image_name):
            image_bytes = os.path.getsize(local_image_name)
            if image_bytes <= 0 or image_bytes > config.max_image_bytes:
                return None
            identify = config.imagemagick_identify_path
            try:
                image_details = self.get_image_dimensions(identify, local_image_name)
            except (OSError, ValueError):
                return None
            file_extension = self.get_mime_type(image_details)
            return LocallyStoredImage(
                src=src,
                local_filename=local_image_name,
                link_hash=link_hash,
                bytes=image_bytes,
                file_extension=file_extension,
                height=image_details.get_height(),
                width=image_details.get_width()
            )
        return None

    @classmethod
    def write_localfile(self, entity, link_hash, src, config):
        local_path = self.get_localfile_name(link_hash, src, config)
        with open(local_path, 'wb') as image_file:
            image_file.write(entity)
        try:
            image = self.read_localfile(link_hash, src, config)
        except Exception:
            self._remove_localfile(local_path)
            raise
        if image is None:
            self._remove_localfile(local_path)
        return image

    @classmethod
    def _remove_localfile(self, path):
        try:
            os.remove(path)
        except FileNotFoundError:
            pass

    @classmethod
    def get_localfile_name(self, link_hash, src, config):
        image_hash = hashlib.md5(smart_str(src)).hexdigest()
        return os.path.join(config.local_storage_path, '%s_%s' % (link_hash, image_hash))

    @classmethod
    def clean_src_string(self, src):
        return src.replace(" ", "%20")

    @classmethod
    def fetch(self, http_client, src, config):
        try:
            return fetch_bytes(
                config,
                src,
                config.max_image_bytes,
                accepted_content_types={"image/*"},
            )
        except (HTTPError, URLError, OSError, HTTPException, ValueError):
            return None
