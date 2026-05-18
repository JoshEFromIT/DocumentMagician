# DocumentMagician

Generate detailed technical markdown documentation from local code files and URLs using a **local LLM** (via Ollama) on your MacBook Pro M4.

## Features

- Accepts one or more local files and/or URLs as input.
- Uses a local Ollama model (no cloud LLM required).
- Produces a structured, high-detail markdown document.
- Supports dry-run mode to inspect the prompt template.

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com/) running locally (`ollama serve`)
- One of your local models, for example:
  - `systemlens-llama31:latest`
  - `mistralnemo:docs8k` (default)
  - `qwen3.6-local:latest`
  - `qwen3-coder:30b`
  - `qwen3-vl:8b`
  - `granite-vision:2b-q8_0`
  - `nomic-local:latest`

## Quick start

```bash
cd /path/to/DocumentMagician
python3 document_magician.py --help
```

Generate a document from files + URLs:

```bash
python3 document_magician.py \
  /absolute/path/to/main.py /absolute/path/to/service.ts \
  --url "https://example.com/spec" \
  --model "mistralnemo:docs8k" \
  --num-ctx 8192 \
  --title "AI Project Documentation" \
  --output ./generated_document.md
```

Dry run (no model call, writes the generated prompt):

```bash
python3 document_magician.py /absolute/path/to/main.py --dry-run --output ./prompt_preview.md
```

## Notes

- Inputs are truncated per source (default `--max-chars 20000`) to keep prompts manageable.
- If Ollama is unreachable, start it and verify your model is installed:

```bash
ollama serve
ollama list
```
