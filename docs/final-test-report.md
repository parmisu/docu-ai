# Docu AI Final Test Report

## Executive Summary

Docu AI began as a functional local PDF question-answering prototype.

The engineering hardening process added controlled fixtures, automated tests, evaluation datasets, reproducibility evidence, lifecycle tests, error handling, retrieval metrics, citation checks, end-to-end integration tests, and continuous integration.

The final test system is designed to expose both successful behavior and unresolved limitations.

## Baseline

The original baseline evaluation used a single manually tested PDF question.

The baseline demonstrated that the application could:

- process a PDF
- create a vector store
- retrieve document chunks
- generate an answer
- display source pages

The observed baseline end-to-end interaction took approximately 25 seconds on the development machine for the controlled test.

At baseline there was no formal reference dataset, Recall@5, MRR@5, citation-accuracy metric, abstention metric, reproducible pytest suite, or CI workflow.

## Final Evaluation Coverage

The final reference dataset contains 32 questions covering:

- direct factual retrieval
- multi-part questions
- irrelevant questions
- unanswerable questions
- conflicting evidence

The final evaluation measures retrieval, answer correctness, citations, abstention, reproducibility, performance, lifecycle behavior, error recovery, and end-to-end integration.

## Final Metrics

Current recorded evaluation results include:

- Macro Recall@5: approximately `0.8893`
- MRR@5: approximately `0.7417`
- Answer correctness: `0.75`
- Full citation accuracy: `0.80`
- Mean citation coverage: `0.8893`
- Abstention accuracy: `1.00`
- Overall answer-evaluation pass rate: `0.75`

These values represent the controlled evaluation dataset and should not be interpreted as universal production guarantees.

## Improvements From Baseline

The final project adds evidence that did not exist in the original prototype:

- deterministic PDF extraction tests
- page-order tests
- empty and image-only PDF handling
- corrupted PDF handling
- file-signature validation
- extraction edge-case tests
- large-document performance testing
- chunk boundary and overlap tests
- metadata traceability
- deduplication tests
- vector-store correctness
- direct and multi-part retrieval tests
- irrelevant retrieval tests
- threshold experiments
- document isolation
- duplicate-upload caching
- document replacement and deletion lifecycle
- persistence behavior documentation
- answer correctness evaluation
- abstention testing
- citation accuracy testing
- multi-source citation testing
- conflicting-evidence handling
- reproducibility analysis
- Ollama error handling
- input validation
- application-state recovery
- reference evaluation dataset
- retrieval metrics
- final answer metrics
- reproducible pytest reporting
- simulated and real Ollama integration testing
- GitHub Actions CI

## Pytest

Pytest configuration is defined in:

`pytest.ini`

Independent tests run without requiring a live Ollama service.

Tests requiring real Ollama are explicitly marked as integration tests.

Machine-readable and terminal-readable reports are stored in:

- `artifacts/pytest-report.xml`
- `artifacts/pytest-output.txt`

The committed reports represent an actual pytest execution rather than manually edited status values.

## Continuous Integration

GitHub Actions runs the independent test suite for pushes and pull requests targeting `main`.

The workflow:

- installs Python 3.11
- installs project dependencies
- runs `pip check`
- runs independent pytest tests
- generates JUnit XML
- captures terminal pytest output
- uploads reports even when tests fail

Real local-Ollama integration remains separate because GitHub-hosted CI does not have access to the developer's local Ollama service.

## Known Open Issues

### Multi-part retrieval

Some questions requiring multiple independent evidence sections do not retrieve every required section within the top five results.

Known affected cases include:

- `eval-013`
- `eval-016`
- `eval-017`
- `eval-018`

### Answer-generation failures

The final evaluation contains cases where relevant evidence is retrieved but the model still produces an incomplete or incorrect answer.

### Conflicting evidence

The dedicated conflict test succeeds, but the broader final evaluation still fails the two conflict cases.

Conflict handling is therefore not consistently robust across prompts and contexts.

### Vector-store persistence

The current Chroma vector store is runtime-scoped.

A full application restart requires reprocessing and re-embedding the PDF.

### OCR

Image-only and scanned PDFs are detected as containing no extractable text.

OCR is not implemented.

### Local-model dependency

Real answer generation depends on a running Ollama service and the `llama3.2:3b` model.

Model availability, local resources, and service state can affect integration behavior.

### Retrieval threshold and ranking

The current retrieval configuration is empirically tested but not globally optimal.

Different document domains may require different chunking, ranking, or threshold settings.

## Performance

A controlled 50-page text PDF completed extraction well below the predefined 10-second extraction threshold on the development machine.

A larger real-world PDF with approximately 991 pages was also processed without crashing, although retrieval quality on the tested question was not sufficient to answer successfully.

Exact memory profiling has not been implemented.

## Reproduction

Activate the project environment:

```bash
source .venv/bin/activate
```

Run independent tests:

```bash
python -m pytest -m "not integration" -v
```

Generate pytest evidence:

```bash
set -o pipefail
python -m pytest -m "not integration" -v \
  --junitxml=artifacts/pytest-report.xml \
  2>&1 | tee artifacts/pytest-output.txt
```

Run real Ollama integration:

```bash
RUN_OLLAMA_TESTS=1 python -m pytest -m integration -v
```

Run retrieval evaluation:

```bash
python evaluation/run_retrieval_evaluation.py
```

Run answer evaluation:

```bash
python evaluation/run_answer_evaluation.py
```

## Final Assessment

The project has moved from a working RAG prototype to a substantially tested local AI system with explicit evidence for correctness, failure handling, retrieval quality, citation behavior, lifecycle behavior, reproducibility, and integration.

The final results also identify unresolved weaknesses rather than hiding them.

The strongest measured behavior is abstention on unsupported questions and generally high citation/evidence coverage.

The main remaining engineering opportunities are stronger multi-part retrieval, more reliable conflict reasoning, durable vector-store persistence, OCR support, and broader evaluation on less-controlled real-world documents.