from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.error import URLError
from urllib.request import Request, urlopen


@dataclass(slots=True)
class SourceDocument:
    source_type: str
    source_name: str
    content: str


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style"} and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            text = data.strip()
            if text:
                self._parts.append(text)

    def text(self) -> str:
        return "\n".join(self._parts)


def read_files(paths: Iterable[str], max_chars: int) -> list[SourceDocument]:
    documents: list[SourceDocument] = []
    for raw_path in paths:
        path = Path(raw_path).expanduser().resolve()
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")
        content = path.read_text(encoding="utf-8", errors="replace")[:max_chars]
        documents.append(SourceDocument("file", str(path), content))
    return documents


def fetch_urls(urls: Iterable[str], max_chars: int, timeout_seconds: int = 20) -> list[SourceDocument]:
    documents: list[SourceDocument] = []
    for url in urls:
        request = Request(url, headers={"User-Agent": "DocumentMagician/0.1"})
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                html = response.read().decode(charset, errors="replace")
        except URLError as exc:
            raise RuntimeError(f"Failed to fetch URL '{url}': {exc}") from exc

        parser = _HTMLTextExtractor()
        parser.feed(html)
        text_content = parser.text()[:max_chars]
        documents.append(SourceDocument("url", url, text_content))
    return documents
