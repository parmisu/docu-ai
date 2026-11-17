# Reproducibility Evaluation Report

## Purpose

This experiment measures answer variation across repeated controlled runs of the same questions.

The goal is not to require guaranteed bit-for-bit identical language-model output.

Instead, the experiment records the model, settings, prompt, runtime conditions, and observed answer differences.

## Execution Configuration

- Model: `llama3.2:3b`
- Temperature: `0`
- Runs per question: `3`
- Python: `3.11.17 (main, Oct  1 2026, 00:48:48) [Clang 21.0.0 (clang-2100.3.34.2)]`
- Platform: `macOS-26.6-arm64-arm-64bit`
- Machine architecture: `arm64`

### Ollama Version

```text
ollama version is 0.40.16
```

### Installed Ollama Models

```text
NAME           ID              SIZE      MODIFIED    
llama3.2:3b    a80c4f17acd5    2.0 GB    4 weeks ago    
llama3.2:1b    baf6a787fdff    1.3 GB    5 weeks ago
```

## Prompt

```text
Use only the context below.

Return the shortest exact answer that directly answers
the question.

Prefer words or phrases that appear explicitly in the
context.

Do not answer with the name of the application unless
the question specifically asks for the application.

If the context does not contain the answer, respond:
ANSWER NOT FOUND

Context:
{context}

Question:
{question}

Answer:
```

## Results Summary

- Total question cases: `4`
- Cases with identical exact output across runs: `4`
- Cases with identical normalized output across runs: `4`

## Per-Question Results

### answer-001

Question: What database stores vector embeddings in Docu AI?

- Exact output stable: `True`
- Normalized output stable: `True`
- Unique exact answers: `1`

Run 1:

```text
ChromaDB
```

Run 2:

```text
ChromaDB
```

Run 3:

```text
ChromaDB
```

### answer-002

Question: Which tool runs the local language model?

- Exact output stable: `True`
- Normalized output stable: `True`
- Unique exact answers: `1`

Run 1:

```text
ANSWER NOT FOUND
```

Run 2:

```text
ANSWER NOT FOUND
```

Run 3:

```text
ANSWER NOT FOUND
```

### answer-003

Question: What framework provides the user interface?

- Exact output stable: `True`
- Normalized output stable: `True`
- Unique exact answers: `1`

Run 1:

```text
Streamlit
```

Run 2:

```text
Streamlit
```

Run 3:

```text
Streamlit
```

### answer-004

Question: What information is kept for source traceability?

- Exact output stable: `True`
- Normalized output stable: `True`
- Unique exact answers: `1`

Run 1:

```text
Source document name and page number.
```

Run 2:

```text
Source document name and page number.
```

Run 3:

```text
Source document name and page number.
```

## Interpretation

Temperature was fixed at zero to reduce sampling variation, but this test does not assume that local LLM execution is technically guaranteed to produce identical text on every run.

Exact-match differences may include wording, punctuation, or formatting changes that do not necessarily change the semantic answer.

Normalized comparison is therefore reported separately from exact-string comparison.

Any observed differences should be reviewed for semantic impact rather than treated automatically as correctness failures.

## Conclusion

This experiment documents the observed repeatability of the current Docu AI answer-generation configuration.

Reproducibility is evaluated empirically under controlled settings rather than assuming guaranteed deterministic output.