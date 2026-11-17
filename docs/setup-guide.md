# Setup Guide

This guide documents the verified steps required to install and run Docu AI from a clean local environment.

## Prerequisites

- Python 3.11
- Git
- Ollama

## 1. Clone the Repository

```bash
git clone https://github.com/parmisu/docu-ai.git
cd docu-ai

## Ollama Troubleshooting

Docu AI requires a running local Ollama service and the configured model:

```text
llama3.2:3b
```

Check that Ollama is available:

```bash
ollama --version
```

Check installed models:

```bash
ollama list
```

If `llama3.2:3b` is missing, install it with:

```bash
ollama pull llama3.2:3b
```

### Ollama is not running

If Docu AI cannot connect to Ollama, make sure the Ollama service is running and retry the request.

### Model not installed

If the configured model cannot be found, run:

```bash
ollama pull llama3.2:3b
```

and retry.

### Request timeout

A slow model response may occur with limited system resources or large workloads.

Retry the request. If the problem continues, restart Ollama or try a smaller document.

### Invalid or empty model response

Docu AI treats empty or structurally invalid model responses as failures rather than valid answers.

Retry the request. If the problem continues, restart Ollama.

### Ollama service error

If Ollama reports an internal service error, retry the request and restart Ollama if necessary.

Docu AI does not treat these failure states as successful answers.