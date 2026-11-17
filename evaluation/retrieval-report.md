# Retrieval Evaluation Report

## Purpose

This evaluation measures whether the expected evidence sections are retrieved within the top five results.

## Metrics

### Recall@5

For each question:

```text
Recall@5 = relevant reference sections retrieved in top 5 / total reference sections
```

The reported dataset-level Recall@5 is the macro average across eligible questions.

### MRR@5

For each question:

```text
RR@5 = 1 / rank of the first relevant result
```

If no relevant result appears in the top five, the reciprocal rank is 0.

MRR@5 is the mean reciprocal rank across eligible evaluation questions.

## Eligibility

Only questions with explicit expected reference sections are included in retrieval metrics.

Unanswerable and irrelevant questions are excluded because they intentionally have no reference source.

Including them as retrieval failures would misrepresent retrieval quality.

## Sample Counts

- Evaluated questions: `20`
- Excluded questions: `12`
- Top K: `5`

## Aggregate Results

- Macro Recall@5: `0.8893`
- MRR@5: `0.7417`
- Perfect-recall questions: `16`
- Questions with retrieval misses: `4`

## Failure Analysis

### eval-013

How does Docu AI retrieve information and generate an answer?

- Recall@5: `0.5000`
- RR@5: `0.3333`
- Missed markers: `GENERATION_MARKER`

### eval-016

What provides the user interface and what metadata supports traceability?

- Recall@5: `0.5000`
- RR@5: `0.5000`
- Missed markers: `STREAMLIT_SOURCE`

### eval-017

Which components handle embedding, storage, retrieval, and answer generation?

- Recall@5: `0.5000`
- RR@5: `1.0000`
- Missed markers: `RETRIEVAL_MARKER, GENERATION_MARKER`

### eval-018

What happens from PDF upload through source traceability?

- Recall@5: `0.2857`
- RR@5: `1.0000`
- Missed markers: `EMBEDDING_MARKER, STORAGE_MARKER, RETRIEVAL_MARKER, GENERATION_MARKER, SOURCE_MARKER`

## Per-Question Summary

| ID | Type | Expected | Found | Recall@5 | RR@5 |
|---|---|---:|---:|---:|---:|
| eval-001 | direct | 1 | 1 | 1.0000 | 1.0000 |
| eval-002 | direct | 1 | 1 | 1.0000 | 0.5000 |
| eval-003 | direct | 1 | 1 | 1.0000 | 0.5000 |
| eval-004 | direct | 1 | 1 | 1.0000 | 0.5000 |
| eval-005 | direct | 1 | 1 | 1.0000 | 1.0000 |
| eval-006 | direct | 1 | 1 | 1.0000 | 1.0000 |
| eval-007 | direct | 1 | 1 | 1.0000 | 1.0000 |
| eval-008 | direct | 1 | 1 | 1.0000 | 0.3333 |
| eval-009 | direct | 1 | 1 | 1.0000 | 0.3333 |
| eval-010 | direct | 1 | 1 | 1.0000 | 1.0000 |
| eval-011 | multi-part | 2 | 2 | 1.0000 | 1.0000 |
| eval-012 | multi-part | 2 | 2 | 1.0000 | 0.3333 |
| eval-013 | multi-part | 2 | 1 | 0.5000 | 0.3333 |
| eval-014 | multi-part | 2 | 2 | 1.0000 | 1.0000 |
| eval-015 | multi-part | 2 | 2 | 1.0000 | 0.5000 |
| eval-016 | multi-part | 2 | 1 | 0.5000 | 0.5000 |
| eval-017 | multi-part | 4 | 2 | 0.5000 | 1.0000 |
| eval-018 | multi-part | 7 | 2 | 0.2857 | 1.0000 |
| eval-031 | conflicting | 2 | 2 | 1.0000 | 1.0000 |
| eval-032 | conflicting | 2 | 2 | 1.0000 | 1.0000 |

## Interpretation

Recall@5 measures evidence coverage, including multi-section questions.

MRR@5 measures how early the first relevant section appears in the ranked results.

The detailed CSV should be used to inspect ranking errors and individual retrieved chunks.

## Reproducibility

The evaluation uses the fixed reference dataset in `evaluation/dataset.jsonl`, the controlled fixture corpus, `k=5`, and the configured `all-MiniLM-L6-v2` embedding model.