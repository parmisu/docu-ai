# Retrieval Threshold Experiment Report

## Purpose

This experiment evaluates several retrieval-score thresholds using a fixed set of relevant and irrelevant questions.

The goal is to determine whether a single threshold can reliably distinguish document-supported retrieval results from results that are merely semantically similar.

## Metric Direction

Docu AI uses:

```python
similarity_search_with_relevance_scores(...)
```

The experiment therefore treats the returned value as a relevance/similarity score.

The comparison direction is:

```text
higher score = more relevant
```

A result is accepted when:

```python
score >= threshold
```

This is different from a distance-based metric, where lower values would normally indicate greater similarity.

## Thresholds Evaluated

The experiment compared:

```text
0.00
0.05
0.10
0.15
0.20
0.25
0.30
0.40
0.50
```

The full results are stored in:

`evaluation/threshold-results.csv`

## Important Observed Scores

Relevant questions produced scores including:

```text
Chroma retrieval question     0.683912
Embedding question            0.636785
Ollama question               0.510870
Streamlit interface question  0.011785
```

Irrelevant or unsupported questions produced scores including:

```text
Chroma monthly-price question  0.661953
Streamlit founder question     0.040787
Weather question              -0.303602
```

## Key Finding

The score distributions overlap substantially.

A particularly important comparison is:

```text
Relevant Streamlit result:
0.011785

Unsupported Chroma pricing result:
0.661953
```

The unsupported pricing question receives a much higher similarity score than one of the valid relevant questions.

Therefore, no single tested threshold can perfectly separate supported and unsupported questions.

## Behavior of the Current Threshold

Docu AI currently uses:

```text
0.15
```

At this threshold, the experiment shows both types of error.

### False Negative

The relevant Streamlit interface question has:

```text
score = 0.011785
```

Because:

```text
0.011785 < 0.15
```

the relevant result is rejected.

This is a false negative.

### False Positive

The unsupported Chroma monthly-price question has:

```text
score = 0.661953
```

Because:

```text
0.661953 >= 0.15
```

the result passes the similarity threshold even though the retrieved text contains no evidence about price.

This is a false positive.

## Comparison Across Thresholds

Increasing the threshold removes some weak retrieval results but does not solve the unsupported Chroma pricing case.

For example, the unsupported result remains accepted at:

```text
0.25
0.30
0.40
0.50
```

because its similarity score is approximately:

```text
0.661953
```

At the same time, thresholds above approximately `0.011785` reject the valid Streamlit retrieval result.

This demonstrates that the failure cannot be corrected simply by selecting a higher threshold.

## Final Threshold Decision

The current value:

```text
0.15
```

is retained as a **provisional retrieval threshold**, rather than being treated as a validated answer-confidence boundary.

The experiment does not provide evidence that `0.15` can reliably determine whether a question is answerable from the document.

Instead, it provides a practical filtering value while preserving compatibility with the current Docu AI implementation.

## Required Interpretation

Passing the retrieval threshold must not be interpreted as proof that the retrieved context contains a valid answer.

The retrieval pipeline should distinguish between:

```text
semantic similarity
```

and:

```text
answer-supporting evidence
```

The T21 irrelevant-retrieval tests demonstrate why this additional validation is necessary.

## Recommended Future Improvement

Future versions should combine similarity score with additional evidence checks, such as:

- explicit answer-support validation
- query-to-context entailment checks
- reranking
- stronger retrieval evaluation
- calibrated confidence scoring

The threshold may then be recalibrated using a larger labelled evaluation set.

## Conclusion

T22 shows that retrieval relevance scores are useful for ranking results but are not sufficient by themselves to determine whether the document contains a valid answer.

The tested relevant and irrelevant score distributions overlap.

The existing threshold of `0.15` is therefore retained provisionally, but it must not be treated as an answer-validity threshold.

The experiment provides evidence that Docu AI requires both retrieval scoring and evidence validation to handle unsupported questions reliably.