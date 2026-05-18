#!/usr/bin/env python3
"""Generate detailed project documentation from code files and URLs using a local Ollama model."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_MODEL = "mistralnemo:docs8k"
DEFAULT_OLLAMA_HOST = "http://localhost:11434"

SYSTEM_INSTRUCTIONS = """You are DocumentMagician, an expert technical writer.
Produce a polished markdown document that mirrors the style, depth, and formatting of the provided example style.
Use rich technical detail, concrete examples, and practical implementation guidance.
Always include the exact heading structure from the STYLE AND OUTPUT TEMPLATE section.
"""

OUTPUT_TEMPLATE = """# {title}

## 1) Executive Summary
- What this project is and why it matters.
- Top capabilities and intended users.

## 2) Inputs Reviewed
### 2.1 Code Files
### 2.2 URLs

## 3) Architecture and Core Components
- Explain key modules, responsibilities, and interactions.

## 4) Implementation Details
### 4.1 Data Flow
### 4.2 Key Algorithms/Logic
### 4.3 Error Handling and Edge Cases

## 5) Setup and Run Instructions
- Include prerequisites, commands, and expected output.

## 6) Security, Privacy, and Local-Only Considerations

## 7) Suggested Improvements / Next Iterations

## 8) Appendix
- Important snippets or extracted references.
"""


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self._parts.append(text)

    def get_text(self) -> str:
        return "\n".join(self._parts)


@dataclass
class Source:
    kind: str
    label: str
    content: str


class DocumentMagicianError(RuntimeError):
    """Domain-specific error for user-facing failures."""


def read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise DocumentMagicianError(f"File not found: {path}") from exc
    except OSError as exc:
        raise DocumentMagicianError(f"Unable to read file {path}: {exc}") from exc


def fetch_url_content(url: str, timeout: int = 20) -> str:
    req = Request(url, headers={"User-Agent": "DocumentMagician/1.0"})
    try:
        with urlopen(req, timeout=timeout) as response:  # nosec B310 - user-supplied URL is intentional feature.
            body = response.read().decode("utf-8", errors="replace")
            content_type = response.headers.get("Content-Type", "")
    except (HTTPError, URLError) as exc:
        raise DocumentMagicianError(f"Unable to fetch URL {url}: {exc}") from exc

    if "html" in content_type.lower() or "<html" in body.lower():
        parser = _HTMLTextExtractor()
        parser.feed(body)
        text = parser.get_text()
        return text or body
    return body


def truncate_content(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...[truncated]"


def collect_sources(file_paths: Iterable[str], urls: Iterable[str], max_chars: int = 20000) -> list[Source]:
    sources: list[Source] = []

    for file_path in file_paths:
        path = Path(file_path).expanduser().resolve()
        text = truncate_content(read_text_file(path), max_chars)
        sources.append(Source(kind="file", label=str(path), content=text))

    for url in urls:
        text = truncate_content(fetch_url_content(url), max_chars)
        sources.append(Source(kind="url", label=url, content=text))

    return sources


def build_prompt(sources: list[Source], title: str) -> str:
    if not sources:
        raise DocumentMagicianError("At least one file or URL input is required.")

    source_blocks: list[str] = []
    for source in sources:
        source_blocks.append(
            f"### {source.kind.upper()}: {source.label}\n```\n{source.content}\n```"
        )

    template = OUTPUT_TEMPLATE.format(title=title)

    return (
        f"{SYSTEM_INSTRUCTIONS}\n"
        "STYLE AND OUTPUT TEMPLATE (match this exactly):\n"
        f"{template}\n\n"
        "SOURCE MATERIAL:\n"
        f"{'\n\n'.join(source_blocks)}\n\n"
        "Now produce the final document in markdown only."
    )


def call_ollama(model: str, prompt: str, host: str = DEFAULT_OLLAMA_HOST) -> str:
    endpoint = host.rstrip("/") + "/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"num_ctx": 8192},
    }
    data = json.dumps(payload).encode("utf-8")
    req = Request(endpoint, data=data, headers={"Content-Type": "application/json"}, method="POST")

    try:
        with urlopen(req, timeout=120) as response:
            body = response.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError) as exc:
        raise DocumentMagicianError(
            "Unable to reach local Ollama. Ensure `ollama serve` is running and the model is installed. "
            f"Details: {exc}"
        ) from exc

    try:
        parsed = json.loads(body)
        return parsed["response"].strip()
    except (json.JSONDecodeError, KeyError) as exc:
        raise DocumentMagicianError(f"Unexpected Ollama response: {body[:200]}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a detailed markdown document from code files and URLs using a local Ollama model."
    )
    parser.add_argument("files", nargs="*", help="Code/text files to include in the analysis.")
    parser.add_argument("--url", action="append", default=[], help="URL(s) to include. Can be used multiple times.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Local model name (default: {DEFAULT_MODEL})")
    parser.add_argument("--host", default=DEFAULT_OLLAMA_HOST, help=f"Ollama host (default: {DEFAULT_OLLAMA_HOST})")
    parser.add_argument("--title", default="Generated Technical Project Document", help="Document title")
    parser.add_argument("--output", default="generated_document.md", help="Output markdown file path")
    parser.add_argument("--max-chars", type=int, default=20000, help="Maximum characters to keep per input source")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build and write the prompt to --output without calling Ollama (for validation/debugging).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.files and not args.url:
        print("Error: provide at least one file path or --url input.")
        return 2

    try:
        sources = collect_sources(args.files, args.url, max_chars=args.max_chars)
        prompt = build_prompt(sources, title=args.title)

        if args.dry_run:
            output = prompt
        else:
            output = call_ollama(args.model, prompt, host=args.host)

        output_path = Path(args.output).expanduser().resolve()
        output_path.write_text(output + "\n", encoding="utf-8")
        print(f"Document written to: {output_path}")
        return 0
    except DocumentMagicianError as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
