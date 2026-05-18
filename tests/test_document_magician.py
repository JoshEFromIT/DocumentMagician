import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import document_magician as dm


class DocumentMagicianTests(unittest.TestCase):
    def test_collect_sources_reads_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.py"
            path.write_text("print('hello')\n", encoding="utf-8")

            sources = dm.collect_sources([str(path)], [], max_chars=100)

            self.assertEqual(len(sources), 1)
            self.assertEqual(sources[0].kind, "file")
            self.assertIn("print('hello')", sources[0].content)

    def test_collect_sources_truncates_file_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "long.txt"
            path.write_text("abcdefghij", encoding="utf-8")

            sources = dm.collect_sources([str(path)], [], max_chars=5)

            self.assertIn("...[truncated]", sources[0].content)

    def test_build_prompt_contains_template_and_source(self):
        prompt = dm.build_prompt(
            [dm.Source(kind="file", label="a.py", content="print('x')")],
            title="My Doc",
        )

        self.assertIn("# My Doc", prompt)
        self.assertIn("### FILE: a.py", prompt)
        self.assertIn("Now produce the final document", prompt)

    def test_call_ollama_parses_non_stream_response(self):
        class _FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return json.dumps({"response": "# done"}).encode("utf-8")

        with patch("document_magician.urlopen", return_value=_FakeResponse()):
            output = dm.call_ollama("mistralnemo:docs8k", "prompt")

        self.assertEqual(output, "# done")

    def test_call_ollama_raises_on_bad_json(self):
        class _BadResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return b"{not-json}"

        with patch("document_magician.urlopen", return_value=_BadResponse()):
            with self.assertRaises(dm.DocumentMagicianError):
                dm.call_ollama("mistralnemo:docs8k", "prompt")


if __name__ == "__main__":
    unittest.main()
