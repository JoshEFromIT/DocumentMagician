# DocumentMagician

Local-first technical document generator that accepts code files and URLs, then uses a **local Ollama model only** to produce a polished Markdown document.

## What this project does

- Ingests local code/text files
- Fetches and extracts text from URLs
- Summarizes large inputs in chunks
- Synthesizes a final long-form document in consistent format/detail
- Supports style-matching from a reference file (for “same output/formatting/detail” workflows)

## Requirements

- macOS (Apple Silicon supported, including M4)
- Python 3.10+
- [Ollama](https://ollama.com/) running locally
- One local model available in Ollama, such as:
  - `systemlens-llama31:latest`
  - `mistralnemo:docs8k`
  - `qwen3.6-local:latest`
  - `qwen3-coder:30b`

## Quick start

```bash
cd /home/runner/work/DocumentMagician/DocumentMagician
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Run

```bash
python -m document_magician \
  --files /absolute/path/to/repo/main.py /absolute/path/to/repo/utils.py \
  --urls https://example.com/docs/architecture https://example.com/spec \
  --model qwen3.6-local:latest \
  --title "System Design and Code Walkthrough" \
  --output /absolute/path/to/output/document.md
```

### Match an existing style/format

If you have a sample document style file (for example, text copied from your attached desired format), pass it in:

```bash
python -m document_magician \
  --files /absolute/path/to/repo/main.py \
  --urls https://example.com/docs \
  --model qwen3.6-local:latest \
  --style-reference /absolute/path/to/style_reference.md \
  --output /absolute/path/to/output/document.md
```

## Ollama notes

- This project calls `http://localhost:11434/api/chat`.
- No cloud model APIs are used.
- Ensure model is pulled and available:

```bash
ollama list
```

## CLI options

- `--files`: One or more local file paths
- `--urls`: One or more URLs to ingest
- `--model`: Ollama model name (required)
- `--output`: Output markdown file path (required)
- `--title`: Optional document title
- `--style-reference`: Optional text/markdown file to mirror formatting/detail
- `--ollama-url`: Optional Ollama base URL (default `http://localhost:11434`)
- `--max-source-chars`: Optional source char budget per input (default `12000`)

## Development

Run tests:

```bash
python -m pytest
```
