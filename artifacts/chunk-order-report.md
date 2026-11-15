# Chunk Order Preservation Report

## Purpose

This report documents whether Docu AI preserves the original order of multi-paragraph text during chunking.

The goal is to verify that sentence and paragraph order remain traceable across generated chunks, while distinguishing intentional overlap from accidental deletion or reordering.

## Current Chunking Configuration

Docu AI currently uses:

```python
RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)
```

Current configuration:

- Chunk size: `1000`
- Chunk overlap: `200`

Overlap is expected to duplicate some content between adjacent chunks.

That duplication is intentional and should not be interpreted as a content-ordering error.

## Test Fixture

The controlled source text is stored in:

`tests/fixtures/expected_text/order_case.txt`

The fixture contains multiple paragraphs and uniquely labeled sentences such as:

```text
PARAGRAPH_1_SENTENCE_1
PARAGRAPH_1_SENTENCE_2
PARAGRAPH_2_SENTENCE_1
```

These markers make it possible to track sentence order after chunking.

## Test File

Automated tests:

`tests/test_chunk_order.py`

The test suite verifies that:

- original sentence markers remain present after chunking
- marker order is preserved
- overlap does not cause content to appear in reverse order
- duplicate content caused by overlap is not treated as missing or reordered content
- source and page metadata remain attached to chunks

## Order Verification

The expected marker sequence is taken directly from the original fixture.

Markers found across the generated chunks are compared against the original ordering.

Intentional duplicate markers caused by overlap are handled separately from the first occurrence of each original marker.

This prevents overlap duplication from being incorrectly interpreted as reordered content.

## Content Preservation

Each original marker must remain discoverable somewhere across the generated chunks.

This confirms that chunking has not silently removed any of the controlled source sections.

## Metadata Preservation

All generated chunks retain:

- source metadata
- page-number metadata

This allows later retrieval stages to trace chunk content back to its original document location.

## Test Execution

Command:

```bash
python -m pytest tests/test_chunk_order.py -v
```

Observed result:

```text
4 passed
```

## Repeated Execution

The same test suite was executed again without changing the fixture or implementation.

Observed result:

```text
4 passed
```

The repeated execution produced the same passing behavior.

## Result

The tested multi-paragraph input preserved its original content order after chunking.

Intentional overlap duplication did not cause the source sequence to be reversed or interpreted as missing content.

## Conclusion

T15 confirms that the current chunking pipeline preserves original sentence and paragraph order for the controlled multi-paragraph fixture.

Overlap introduces expected duplication between chunks, but the original sequence and content remain traceable.