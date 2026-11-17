# Evaluation Dataset Review

## Dataset Summary

The Docu AI reference evaluation dataset contains:

```text
32 total questions
```

The dataset intentionally includes multiple retrieval and answer-generation conditions rather than only straightforward questions.

## Category Coverage

Current coverage:

| Question Type | Count |
|---|---:|
| Direct | 10 |
| Multi-part | 8 |
| Unanswerable | 6 |
| Irrelevant | 6 |
| Conflicting | 2 |
| **Total** | **32** |

## Direct Questions

Direct questions evaluate whether a single clearly relevant section can be retrieved and used correctly.

They cover:

- ChromaDB
- Ollama
- Streamlit
- embeddings
- extraction
- retrieval
- answer generation
- source metadata
- PDF upload

## Multi-Part Questions

Multi-part questions require evidence from more than one section or source.

They test combinations including:

- upload + extraction
- embedding + storage
- retrieval + generation
- retrieval + traceability
- ChromaDB + Ollama
- Streamlit + metadata
- full retrieval pipeline

These cases prevent evaluation from being limited to single-chunk factual lookup.

## Unanswerable Questions

Unanswerable questions are related to Docu AI or its technologies but request information not provided by the controlled corpus.

Examples include:

- pricing
- founder information
- country of creation
- release year

Expected behavior is abstention.

## Irrelevant Questions

Irrelevant questions are intentionally unrelated to the indexed document corpus.

Examples include:

- weather
- sports
- geography
- cooking
- current exchange rates

These cases test whether semantic retrieval results are incorrectly treated as valid evidence.

## Conflicting Evidence

Two cases use conflicting Nova protocol sources.

Source A states:

```text
30 seconds
```

Source B states:

```text
60 seconds
```

The expected answer must expose the disagreement rather than select one claim without additional evidence.

## Traceability Review

Every answerable record includes:

- stable evaluation ID
- question type
- reference answer
- expected source
- expected page or section
- stable evidence marker

Unsupported records explicitly contain no expected evidence.

This makes each evaluation result traceable back to its intended evidence condition.

## Repeatability

The dataset is stored as JSONL so every record can be parsed independently.

Stable IDs allow results from separate evaluation runs to be compared without depending on row position.

Controlled source names, pages, and markers reduce ambiguity when validating retrieval and citation results.

## Review Outcome

The dataset satisfies the minimum size requirement of 30 questions.

It contains coverage for:

- direct questions
- multi-part questions
- irrelevant questions
- unanswerable questions
- conflicting evidence

The dataset is suitable as the reference set for subsequent retrieval, citation, answer-quality, abstention, and end-to-end evaluations.