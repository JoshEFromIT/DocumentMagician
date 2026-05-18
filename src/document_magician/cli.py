from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .generator import DocumentGenerator
from .ingest import SourceDocument, fetch_urls, read_files
from .llm import OllamaClient


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="document-magician",
        description="Generate a technical markdown document from files + URLs using local Ollama models.",
    )
    parser.add_argument("--files", nargs="*", default=[], help="Absolute/relative file paths to ingest.")
    parser.add_argument("--urls", nargs="*", default=[], help="URLs to fetch and ingest.")
    parser.add_argument("--model", required=True, help="Local Ollama model name.")
    parser.add_argument("--output", required=True, help="Output markdown file path.")
    parser.add_argument("--title", default=None, help="Optional output document title.")
    parser.add_argument(
        "--style-reference",
        default=None,
        help="Optional path to a style reference document to match formatting/detail.",
    )
    parser.add_argument(
        "--ollama-url",
        default="http://localhost:11434",
        help="Ollama base URL.",
    )
    parser.add_argument(
        "--max-source-chars",
        type=int,
        default=12000,
        help="Max characters to ingest per source.",
    )
    return parser.parse_args()


def _load_style_reference(path: str | None) -> str | None:
    if not path:
        return None
    style_path = Path(path).expanduser().resolve()
    return style_path.read_text(encoding="utf-8", errors="replace")


def _collect_sources(file_paths: list[str], urls: list[str], max_source_chars: int) -> list[SourceDocument]:
    sources: list[SourceDocument] = []
    if file_paths:
        sources.extend(read_files(file_paths, max_chars=max_source_chars))
    if urls:
        sources.extend(fetch_urls(urls, max_chars=max_source_chars))
    return sources


def main() -> int:
    args = _parse_args()
    if not args.files and not args.urls:
        print("Provide at least one input via --files or --urls.", file=sys.stderr)
        return 2

    try:
        style_reference = _load_style_reference(args.style_reference)
        sources = _collect_sources(args.files, args.urls, args.max_source_chars)
        if not sources:
            print("No usable source content was loaded.", file=sys.stderr)
            return 3

        client = OllamaClient(model=args.model, base_url=args.ollama_url)
        generator = DocumentGenerator(llm=client)
        markdown = generator.build_document(
            sources=sources,
            title=args.title,
            style_reference=style_reference,
        )

        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        print(f"Document written to: {output_path}")
        return 0
    except Exception as exc:  # pragma: no cover
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
