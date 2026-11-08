"""Offline tests for the pyteaser command-line interface."""

import json
import os
import subprocess
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest import TestCase
from unittest import main as unittest_main

from pyteaser import main


class TestCLI(TestCase):
    def test_cli_summarizes_text_and_input_files(self):
        text_output = StringIO()
        with redirect_stdout(text_output):
            status = main(
                [
                    "--title",
                    "CLI example",
                    "--text",
                    "One sentence. Two sentence.",
                    "--sentence-count",
                    "1",
                ]
            )
        self.assertEqual(status, 0)
        self.assertEqual(len(text_output.getvalue().strip().splitlines()), 1)

        with tempfile.TemporaryDirectory() as temporary_directory:
            article_file = os.path.join(temporary_directory, "article.txt")
            with open(article_file, "w", encoding="utf-8") as source:
                source.write("File sentence one. File sentence two.")
            file_output = StringIO()
            with redirect_stdout(file_output):
                status = main(["--input-file", article_file, "--max-words", "3"])

        self.assertEqual(status, 0)
        self.assertTrue(file_output.getvalue().strip())

    def test_cli_is_runnable_as_a_module(self):
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "pyteaser",
                "--text",
                "One sentence only.",
                "--sentence-count",
                "1",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        self.assertEqual(completed.stdout.strip(), "One sentence only.")

    def test_cli_rejects_title_with_url_input(self):
        error_output = StringIO()
        with redirect_stderr(error_output):
            with self.assertRaises(SystemExit) as error:
                main(["--url", "https://example.test/a", "--title", "Unused"])

        self.assertEqual(error.exception.code, 2)
        self.assertIn("--title", error_output.getvalue())

    def test_cli_json_output_reports_scores(self):
        json_output = StringIO()
        with redirect_stdout(json_output):
            status = main(
                [
                    "--title",
                    "CLI example",
                    "--text",
                    "One sentence. Two sentence.",
                    "--sentence-count",
                    "1",
                    "--json",
                ]
            )

        self.assertEqual(status, 0)
        payload = json.loads(json_output.getvalue())
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["sentence"], "Two sentence.")
        self.assertEqual(payload[0]["index"], 1)
        self.assertIsInstance(payload[0]["score"], float)

    def test_cli_reports_the_version(self):
        version_output = StringIO()
        with redirect_stdout(version_output):
            with self.assertRaises(SystemExit) as error:
                main(["--version"])

        self.assertEqual(error.exception.code, 0)
        self.assertIn("pyteaser", version_output.getvalue())

    def test_cli_reports_url_errors_without_a_traceback(self):
        error_output = StringIO()
        with redirect_stderr(error_output):
            with self.assertRaises(SystemExit) as error:
                main(["--url", "file:///etc/passwd"])

        self.assertEqual(error.exception.code, 2)
        self.assertIn("Could not fetch", error_output.getvalue())


if __name__ == "__main__":
    unittest_main()
