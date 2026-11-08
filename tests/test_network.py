"""Offline tests for the goose network policy."""

import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO
from threading import Thread
from types import SimpleNamespace
from unittest import TestCase
from unittest import main as unittest_main
from unittest.mock import MagicMock, patch
from urllib.request import Request

from goose.configuration import Configuration
from goose.network import (
    FetchError,
    HtmlFetcher,
    SafeRedirectHandler,
    _read_limited,
    _SafeHTTPConnection,
    fetch_bytes,
    validate_url,
)


class TestNetworkPolicy(TestCase):
    def test_allows_public_http_url(self):
        self.assertEqual(validate_url("https://1.1.1.1/").scheme, "https")

    def test_rejects_non_http_scheme(self):
        with self.assertRaises(ValueError):
            validate_url("file:///etc/passwd")

    def test_rejects_private_ip(self):
        with self.assertRaises(ValueError):
            validate_url("http://127.0.0.1/")

    @patch(
        "goose.network.socket.getaddrinfo",
        return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))],
    )
    def test_rejects_hostname_resolving_to_private_ip(self, getaddrinfo):
        with self.assertRaises(ValueError):
            validate_url("https://article.example/")
        getaddrinfo.assert_called_once()

    def test_redirect_handler_rejects_private_target(self):
        handler = SafeRedirectHandler()
        with self.assertRaises(ValueError):
            handler.redirect_request(
                Request("https://1.1.1.1/"),
                None,
                302,
                "Found",
                {},
                "http://127.0.0.1/",
            )

    def test_read_limit_rejects_oversized_response(self):
        with self.assertRaises(ValueError):
            _read_limited(BytesIO(b"12345"), 4)

    @patch("goose.network.socket.create_connection")
    @patch(
        "goose.network.socket.getaddrinfo",
        return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 80))],
    )
    def test_http_connection_uses_the_validated_ip(
        self, getaddrinfo, create_connection
    ):
        connection = _SafeHTTPConnection("article.example", 80, timeout=2)

        connection.connect()

        create_connection.assert_called_once_with(
            ("1.1.1.1", 80), timeout=2, source_address=None
        )
        getaddrinfo.assert_called_once()

    @patch("goose.network.build_opener")
    def test_fetch_bytes_applies_timeout_and_content_type(self, build_opener_mock):
        config = SimpleNamespace(
            browser_user_agent="PyTeaser test",
            request_timeout=2.5,
            allow_private_network=False,
        )
        response = MagicMock()
        response.__enter__.return_value = response
        response.geturl.return_value = "https://1.1.1.1/"
        response.headers.get_content_type.return_value = "text/html"
        response.read.return_value = b"page"
        opener = build_opener_mock.return_value
        opener.open.return_value = response

        content = fetch_bytes(config, "https://1.1.1.1/", 4, {"text/html"})

        self.assertEqual(content, b"page")
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 2.5)

    def test_html_fetcher_raises_typed_fetch_error(self):
        with patch("goose.network.fetch_bytes", side_effect=ValueError("blocked")):
            with self.assertRaises(FetchError):
                HtmlFetcher().get_html(Configuration(), "https://example.test/")

    def test_fetches_from_loopback_when_explicitly_allowed(self):
        body = b"<html>local test</html>"

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)

        config = SimpleNamespace(
            browser_user_agent="PyTeaser test",
            request_timeout=2,
            allow_private_network=True,
        )
        url = "http://127.0.0.1:%s/" % server.server_port

        self.assertEqual(fetch_bytes(config, url, 1024, {"text/html"}), body)


if __name__ == "__main__":
    unittest_main()
