from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .ingest import SourceDocument
from .llm import OllamaClient


def _chunk_text(text: str, chunk_size: int = 5000) -> list[str]:
    if not text:
        return []
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


@dataclass(slots=True)
class DocumentGenerator:
    llm: OllamaClient

    def build_document(
        self,
        sources: Iterable[SourceDocument],
        title: str | None = None,
        style_reference: str | None = None,
    ) -> str:
        summarized_sources: list[str] = []
        for source in sources:
            chunks = _chunk_text(source.content)
            if not chunks:
                continue
            chunk_summaries: list[str] = []
            for idx, chunk in enumerate(chunks, start=1):
                chunk_prompt = (
                    f"Source type: {source.source_type}\n"
                    f"Source: {source.source_name}\n"
                    f"Chunk: {idx}/{len(chunks)}\n\n"
                    "Summarize this chunk with highly specific technical detail:\n"
                    "- key architecture and behavior\n"
                    "- important implementation details\n"
                    "- API/data flow constraints and assumptions\n"
                    "- notable caveats, edge cases, and risks\n\n"
                    f"{chunk}"
                )
                chunk_summary = self.llm.generate(
                    system_prompt=(
                        "You are an expert technical analyst. "
                        "Create precise, factual summaries with high signal density."
                    ),
                    user_prompt=chunk_prompt,
                )
                chunk_summaries.append(chunk_summary)

            summarized_sources.append(
                f"## Source: {source.source_name}\n\n" + "\n\n".join(chunk_summaries)
            )

        final_prompt = self._build_final_prompt(
            summaries="\n\n".join(summarized_sources),
            title=title,
            style_reference=style_reference,
        )
        return self.llm.generate(
            system_prompt=(
                "You are a principal technical writer. "
                "Produce a polished markdown document that is exhaustive, structured, and clear. "
                "Do not mention using an AI model."
            ),
            user_prompt=final_prompt,
        )

    @staticmethod
    def _build_final_prompt(
        summaries: str, title: str | None, style_reference: str | None
    ) -> str:
        title_line = title or "Technical Document"
        style_block = (
            "\n\nStyle reference to mirror for formatting/detail/tone:\n"
            f"{style_reference}\n"
            if style_reference
            else ""
        )
        return (
            f"Create a complete markdown technical document titled: {title_line}\n\n"
            "Required structure:\n"
            "1. Executive Summary\n"
            "2. Scope and Inputs\n"
            "3. Architecture and Component Breakdown\n"
            "4. Detailed Code/Logic Analysis\n"
            "5. Data Flow and Interfaces\n"
            "6. Risks, Edge Cases, and Gaps\n"
            "7. Actionable Recommendations\n"
            "8. Appendix (source-by-source observations)\n\n"
            "Rules:\n"
            "- Use clear markdown headings and subheadings.\n"
            "- Include concrete specifics from the sources; avoid generic filler.\n"
            "- Keep statements attributable to provided source material.\n"
            "- Keep high detail density and strong technical depth.\n"
            f"{style_block}\n"
            "Source material summaries:\n"
            f"{summaries}"
        )
