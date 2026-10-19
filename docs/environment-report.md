# Environment Report

This document records the verified development environment used for the current version of Docu AI.

## Operating System

- macOS: 26.6
- Build: 25G72
- Architecture: arm64

## Python Runtime

- Python: 3.11.17
- Virtual environment: `.venv`
- Python executable:
  `/Users/parmisu/docu-ai/.venv/bin/python`

## Package Manager

- pip: 26.2.1

## Ollama Runtime

- Ollama: 0.40.6
- Executable:
  `/usr/local/bin/ollama`

## Local Models

The following Ollama models were installed in the verified development environment:

- `llama3.2:3b`
- `llama3.2:1b`

The application is configured to use:

- `llama3.2:3b`

## Direct Python Dependencies

The project directly depends on:

- Streamlit
- PyPDF
- LangChain Core
- LangChain Text Splitters
- LangChain Hugging Face
- LangChain Chroma
- LangChain Ollama
- Sentence Transformers

Exact direct dependency versions are defined in `requirements.txt`.

## Full Dependency Snapshot

A complete pinned snapshot of the verified Python environment is stored in:

`requirements-lock.txt`

This file contains both direct and transitive dependencies.

## Dependency Health

The verified environment was checked with:

```bash
python -m pip check
```

Result:

```text
No broken requirements found.
```