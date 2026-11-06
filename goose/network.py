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
import ipaddress
import socket
from http.cookiejar import CookieJar
from http.client import HTTPConnection, HTTPException, HTTPSConnection
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import (
    HTTPCookieProcessor,
    HTTPHandler,
    HTTPRedirectHandler,
    HTTPSHandler,
    ProxyHandler,
    Request,
    build_opener,
)


class FetchError(IOError):
    """Raised when a page cannot be fetched within the configured policy."""


def _resolve_addresses(host, port, allow_private_network=False):
    """Resolve once, validate every address, and return numeric IP addresses."""
    try:
        addresses = [ipaddress.ip_address(host)]
    except ValueError:
        try:
            resolved = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        except OSError as error:
            raise ValueError("Unable to resolve URL hostname") from error
        addresses = [ipaddress.ip_address(item[4][0]) for item in resolved]

    if not addresses:
        raise ValueError("URL hostname did not resolve to an address")
    if not allow_private_network and any(
            not address.is_global for address in addresses):
        raise ValueError("Private and non-routable network addresses are blocked")
    return [str(address) for address in addresses]


def validate_url(url, allow_private_network=False):
    """Validate an HTTP(S) URL and reject hosts that resolve to local networks."""
    if isinstance(url, bytes):
        url = url.decode("utf-8")
    if not isinstance(url, str):
        raise ValueError("URL must be a string")

    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as error:
        raise ValueError("Invalid URL") from error

    if parsed.scheme.lower() not in ("http", "https"):
        raise ValueError("Only HTTP and HTTPS URLs are supported")
    if not parsed.hostname:
        raise ValueError("URL must include a hostname")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("Credentials in URLs are not allowed")
    expected_port = 443 if parsed.scheme.lower() == "https" else 80
    if port is not None and port != expected_port and not allow_private_network:
        raise ValueError("Only standard HTTP and HTTPS ports are allowed")

    if allow_private_network:
        return parsed

    _resolve_addresses(
        parsed.hostname.rstrip("."), port or expected_port, allow_private_network)
    return parsed


def _create_validated_socket(host, port, timeout, source_address,
                             allow_private_network):
    addresses = _resolve_addresses(host, port, allow_private_network)
    last_error = None
    for address in addresses:
        try:
            return socket.create_connection(
                (address, port), timeout=timeout, source_address=source_address)
        except OSError as error:
            last_error = error
    raise last_error


class _SafeHTTPConnection(HTTPConnection):
    def __init__(self, host, *args, allow_private_network=False, **kwargs):
        self.allow_private_network = allow_private_network
        super().__init__(host, *args, **kwargs)

    def connect(self):
        self.sock = _create_validated_socket(
            self.host, self.port, self.timeout, self.source_address,
            self.allow_private_network)
        if self._tunnel_host:
            self._tunnel()


class _SafeHTTPSConnection(HTTPSConnection):
    def __init__(self, host, *args, allow_private_network=False, **kwargs):
        self.allow_private_network = allow_private_network
        super().__init__(host, *args, **kwargs)

    def connect(self):
        self.sock = _create_validated_socket(
            self.host, self.port, self.timeout, self.source_address,
            self.allow_private_network)
        if self._tunnel_host:
            self._tunnel()
        server_hostname = self._tunnel_host or self.host
        self.sock = self._context.wrap_socket(
            self.sock, server_hostname=server_hostname)


class SafeHTTPHandler(HTTPHandler):
    def __init__(self, allow_private_network=False):
        super().__init__()
        self.allow_private_network = allow_private_network

    def http_open(self, request):
        return self.do_open(
            _SafeHTTPConnection,
            request,
            allow_private_network=self.allow_private_network,
        )


class SafeHTTPSHandler(HTTPSHandler):
    def __init__(self, allow_private_network=False):
        super().__init__()
        self.allow_private_network = allow_private_network

    def https_open(self, request):
        return self.do_open(
            _SafeHTTPSConnection,
            request,
            context=self._context,
            allow_private_network=self.allow_private_network,
        )


class SafeRedirectHandler(HTTPRedirectHandler):
    """Revalidate every redirect target before allowing urllib to follow it."""

    def __init__(self, allow_private_network=False):
        super().__init__()
        self.allow_private_network = allow_private_network

    def redirect_request(self, request, response, code, message, headers, new_url):
        validate_url(new_url, self.allow_private_network)
        return super().redirect_request(
            request, response, code, message, headers, new_url)


def _read_limited(response, max_bytes):
    """Read no more than ``max_bytes`` and fail if the response exceeds it."""
    content = response.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise ValueError("Response exceeds the configured size limit")
    return content


def _content_type_allowed(content_type, allowed_types):
    content_type = (content_type or "").lower()
    return any(
        content_type == allowed
        or (allowed.endswith("/*") and content_type.startswith(allowed[:-1]))
        for allowed in allowed_types
    )


def fetch_bytes(config, url, max_bytes, accepted_content_types=None):
    """Fetch a bounded response using the configured timeout and URL policy."""
    allow_private = bool(getattr(config, "allow_private_network", False))
    if isinstance(url, bytes):
        url = url.decode("utf-8")
    validate_url(url, allow_private)

    timeout = float(getattr(config, "request_timeout", 10.0))
    max_bytes = int(max_bytes)
    if timeout <= 0 or max_bytes <= 0:
        raise ValueError("Timeout and response size limits must be positive")

    opener = build_opener(
        ProxyHandler({}),
        HTTPCookieProcessor(CookieJar()),
        SafeHTTPHandler(allow_private),
        SafeHTTPSHandler(allow_private),
        SafeRedirectHandler(allow_private),
    )
    request = Request(url, headers={"User-agent": config.browser_user_agent})
    with opener.open(request, timeout=timeout) as response:
        validate_url(response.geturl(), allow_private)
        if accepted_content_types:
            content_type = response.headers.get_content_type()
            if not _content_type_allowed(content_type, accepted_content_types):
                raise ValueError("Unexpected response content type: %s" % content_type)
        return _read_limited(response, max_bytes)


class HtmlFetcher:

    def get_html(self, config, url):
        """\
        Fetch an HTML document or raise FetchError when the request fails.
        """
        try:
            return fetch_bytes(
                config,
                url,
                config.max_html_bytes,
                accepted_content_types={"text/html", "application/xhtml+xml"},
            )
        except (HTTPError, URLError, OSError, HTTPException, ValueError) as error:
            raise FetchError("Article HTML could not be fetched safely") from error
