from document_magician.generator import DocumentGenerator
from document_magician.ingest import SourceDocument


class _FakeLLM:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append((system_prompt, user_prompt))
        if "Source type:" in user_prompt:
            return "chunk-summary"
        return "# Final Document\n\nGenerated."


def test_document_generation_calls_chunk_and_final() -> None:
    llm = _FakeLLM()
    generator = DocumentGenerator(llm=llm)  # type: ignore[arg-type]
    result = generator.build_document(
        sources=[SourceDocument(source_type="file", source_name="a.py", content="print('x')")],
        title="My Doc",
    )

    assert result.startswith("# Final Document")
    assert len(llm.calls) == 2
    assert "My Doc" in llm.calls[-1][1]


def test_final_prompt_includes_style_reference() -> None:
    prompt = DocumentGenerator._build_final_prompt(
        summaries="s",
        title="T",
        style_reference="STYLE",
    )
    assert "STYLE" in prompt
    assert "Create a complete markdown technical document titled: T" in prompt
