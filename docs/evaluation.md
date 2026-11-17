# Docu AI Evaluation

## Overview

Docu AI uses a fixed reference evaluation dataset and reproducible evaluation scripts to measure retrieval quality, answer correctness, citation coverage, abstention behavior, conflicting evidence handling, and end-to-end integration.

The evaluation is designed to expose failures rather than hide them behind aggregate metrics.

## Reference Dataset

The reference dataset is stored in:

`evaluation/dataset.jsonl`

It contains 32 controlled questions:

- 10 direct questions
- 8 multi-part questions
- 6 unanswerable questions
- 6 irrelevant questions
- 2 conflicting-evidence questions

Every answerable case defines an expected source, page or section, and stable evidence marker.

Unanswerable and irrelevant cases intentionally contain no expected evidence.

## Retrieval Evaluation

Retrieval evaluation is implemented in:

`evaluation/run_retrieval_evaluation.py`

The evaluation uses:

- `Recall@5`
- `MRR@5`
- top-k = 5
- `sentence-transformers/all-MiniLM-L6-v2`

Only questions with explicit reference evidence are included in retrieval metrics.

Questions intentionally lacking a reference source are excluded rather than incorrectly counted as retrieval failures.

### Retrieval Results

20 questions are eligible for retrieval metrics.

Observed macro Recall@5:

`0.8893`

Observed MRR@5:

`approximately 0.7417`

Most direct questions achieved complete retrieval coverage.

The main retrieval weaknesses appeared in multi-part questions requiring several independent evidence sections.

Known incomplete-retrieval cases include:

- `eval-013`
- `eval-016`
- `eval-017`
- `eval-018`

Detailed results are available in:

- `evaluation/retrieval-metrics.json`
- `evaluation/retrieval-results.csv`
- `evaluation/retrieval-report.md`

## Answer Evaluation

Answer evaluation is implemented in:

`evaluation/run_answer_evaluation.py`

The final controlled run produced:

- answer correctness accuracy: `0.75`
- full citation accuracy: `0.80`
- mean citation coverage: `0.8893`
- abstention accuracy: `1.00`
- overall case pass rate: `0.75`

Detailed per-case results are stored in:

`evaluation/answer-results.jsonl`

## Answer Failures

The final evaluation intentionally preserves unsuccessful cases.

Known answer-generation failures include direct questions where relevant evidence was retrieved but the model did not produce the expected answer.

Known failures also include multi-part questions where some required evidence was missing from the retrieved context.

The final general evaluation also shows weaker handling of conflicting evidence than the dedicated conflict test.

This difference is retained as an engineering limitation rather than being removed from the results.

## Abstention

All 12 unsupported evaluation questions were correctly handled in the final controlled run.

Observed abstention accuracy:

`1.00`

This indicates that the tested prompt successfully avoided assigning unsupported facts to the document for the current reference set.

The result should not be interpreted as a universal guarantee against hallucination.

## Citation Evaluation

Citation checks require more than the presence of a filename or page number.

A controlled citation is considered supported only when:

- the expected document matches
- the page matches
- the retrieved text contains the expected evidence

Multi-source evaluation additionally verifies that separate claims receive the evidence required for each claim.

## Conflicting Evidence

A dedicated controlled test supplies two contradictory sources:

- Source A: 30 seconds
- Source B: 60 seconds

The dedicated conflict-handling test successfully identifies the disagreement and avoids selecting one value as definitively true.

However, the broader final evaluation still contains failures for the conflicting-evidence cases.

This indicates that conflict handling remains prompt-sensitive and is not yet consistently robust across evaluation configurations.

## Reproducibility

Repeated controlled runs are documented in:

- `evaluation/reproducibility-run.py`
- `evaluation/reproducibility-results.jsonl`
- `evaluation/reproducibility-report.md`

The model is run with temperature zero to reduce variation.

The project does not claim that local language-model generation is technically guaranteed to be bit-for-bit deterministic.

## End-to-End Integration

The integration test covers:

PDF → extraction → chunking → embeddings → Chroma → retrieval → answer generation → citation validation.

Two modes are reported independently:

- deterministic simulated integration
- real local Ollama integration

Both controlled integration tests passed in the recorded run.

Detailed results are stored in:

- `evaluation/integration-results.jsonl`
- `artifacts/integration-test-report.md`

## Evaluation Limitations

Automated evaluation is not treated as absolute truth.

Answer correctness uses transparent machine-checkable rules rather than relying exclusively on another language model as a judge.

Lexical or concept-based scoring can still under-score semantically equivalent answers or over-score text that contains the correct vocabulary but is logically wrong.

Citation checks verify controlled source, page, and evidence markers but do not replace human review for nuanced claims.

The current evaluation corpus is intentionally controlled and much smaller than a production-scale benchmark.

## Reproducing Evaluation

Run retrieval evaluation:

```bash
python evaluation/run_retrieval_evaluation.py
```

Run answer evaluation:

```bash
python evaluation/run_answer_evaluation.py
```

Run reproducibility evaluation:

```bash
python evaluation/reproducibility-run.py
```

Run real PDF-to-answer integration:

```bash
RUN_OLLAMA_TESTS=1 python -m pytest tests/integration/test_pdf_to_answer.py -v
```

## Conclusion

The evaluation framework provides reproducible evidence for retrieval, answering, citations, abstention, conflict handling, and integration while retaining known failures for inspection.

The results show strong abstention and generally strong citation/retrieval performance, while multi-part retrieval and consistent conflicting-evidence reasoning remain areas for improvement.