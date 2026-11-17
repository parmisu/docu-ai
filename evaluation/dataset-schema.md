# Evaluation Dataset Schema

## Purpose

`evaluation/dataset.jsonl` is the reference evaluation dataset for Docu AI.

Each JSONL record represents one controlled evaluation question and the evidence expected to support its answer.

Each record is stored on one line to make the dataset easy to parse, version, diff, and reproduce.

## Required Fields

### `id`

Unique stable identifier for the evaluation case.

Example:

```text
eval-001
```

IDs must not be reused for different questions.

### `question`

The question submitted to the retrieval or answer-generation pipeline.

### `question_type`

The evaluation category.

Current allowed values:

```text
direct
multi-part
unanswerable
irrelevant
conflicting
```

#### direct

The answer should be supported by a single clear section.

#### multi-part

The answer requires multiple sections or sources.

#### unanswerable

The question is related to the system or technologies but the required fact is absent from the controlled corpus.

#### irrelevant

The question is outside the scope of the indexed corpus.

#### conflicting

Multiple sources provide incompatible evidence and the expected answer must expose the conflict.

### `reference_answer`

Human-defined expected answer.

For answerable questions this contains the expected factual meaning.

Exact string matching is not required during evaluation.

Equivalent wording may be accepted when the required facts and evidence are preserved.

For unsupported questions:

```json
"reference_answer": null
```

### `expected_sources`

List of source files expected to support the answer.

Example:

```json
["architecture_reference.pdf"]
```

Multi-source questions may contain multiple entries.

For unsupported or irrelevant questions:

```json
[]
```

### `expected_sections`

List of controlled evidence locations.

Each section contains:

```json
{
  "source": "architecture_reference.pdf",
  "page": 2,
  "marker": "CHROMA_SOURCE"
}
```

The marker provides a stable textual identifier in addition to file and page metadata.

For unsupported questions:

```json
[]
```

### `answerable`

Boolean indicating whether the evaluation corpus contains enough evidence to answer the question.

```text
true  = supported answer exists
false = system should abstain
```

### `notes`

Human-readable explanation of the evaluation intent.

This field records why the case exists and helps reviewers distinguish similar cases.

## Traceability Contract

Answerable cases must provide:

```text
question
→ reference answer
→ expected source
→ expected section/page
→ stable evidence marker
```

This allows retrieval, answer correctness, and citation correctness to be evaluated independently.

## Page Numbering

Page metadata uses one-based numbering:

```text
first page = 1
```

## Reproducibility

Evaluation IDs and expected evidence references should remain stable across runs.

If a fixture changes in a way that invalidates an expected marker or page location, the corresponding dataset record must be reviewed and updated explicitly.

## Unsupported Questions

`unanswerable` and `irrelevant` records intentionally contain:

```json
"reference_answer": null,
"expected_sources": [],
"expected_sections": [],
"answerable": false
```

These records evaluate abstention rather than factual answer generation.

## Conflict Cases

Conflicting evidence cases remain technically answerable only when the answer explicitly preserves the disagreement.

The system must not silently choose one source as authoritative unless additional evidence resolves the conflict.