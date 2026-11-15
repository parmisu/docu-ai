# Chunking Boundary Test Report

## Purpose

This report documents the current text chunking behavior in Docu AI, with particular focus on boundary conditions around the configured chunk size.

The goal is to verify that non-empty input text is not unintentionally lost and that behavior near the chunk-size boundary is understood and repeatable.

## Current Chunking Contract

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

The chunk size represents the target maximum chunk length used by the current LangChain text splitter.

Overlap intentionally duplicates some content between adjacent chunks to preserve context across boundaries.

## Test Fixture

Chunking cases are defined in:

`tests/fixtures/chunking_cases.json`

The controlled cases include:

- text shorter than the configured chunk size
- text exactly equal to the configured chunk size
- text slightly larger than the configured chunk size
- very long text

## Test File

Automated tests:

`tests/test_chunking.py`

The test suite verifies:

- non-empty text always produces at least one non-empty chunk
- text shorter than the chunk size remains in a single chunk
- text exactly equal to the chunk size remains in a single chunk
- text slightly larger than the chunk size is split
- very long text produces multiple chunks
- important content markers are not lost during splitting
- source and page metadata remain attached to generated chunks

## Boundary Behavior

### Shorter Than Chunk Size

A 600-character input remains in a single chunk.

### Exactly Chunk Size

A 1000-character input remains in a single chunk.

### Slightly Larger Than Chunk Size

An 1100-character input produces multiple chunks.

### Very Long Text

A 5000-character input produces multiple chunks as expected.

## Content Preservation

The content-preservation test uses explicit markers:

```text
START_MARKER
MIDDLE_MARKER
END_MARKER
```

After chunking, all three markers must still appear across the produced chunks.

This provides a stronger check than simply verifying that chunks are non-empty.

## Metadata Preservation

The generated chunks retain the original document metadata, including:

- source name
- page number

This is important because later retrieval and source attribution depend on this metadata remaining available after chunking.

## Test Execution

Command:

```bash
python -m pytest tests/test_chunking.py -v
```

Observed result:

```text
7 passed
```

## Repeated Execution

The same test suite was executed again without changing the fixtures or implementation.

Observed result:

```text
7 passed
```

The repeated execution produced the same passing behavior.

## Result

The current chunking configuration behaves consistently across the tested boundary cases.

No required marker content was lost, and page/source metadata remained available after splitting.

## Limitations

These tests establish deterministic boundary behavior for controlled text inputs.

They do not yet prove that the current values of:

- `chunk_size=1000`
- `chunk_overlap=200`

are optimal for retrieval quality.

Those values require separate retrieval and evaluation testing.

## Conclusion

T13 establishes the current chunking contract and confirms that the application handles short, exact-boundary, slightly oversized, and long text inputs without unintentionally dropping essential content.