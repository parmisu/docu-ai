# Chunk Overlap Test Report

## Purpose

This report documents the overlap behavior of consecutive text chunks in Docu AI.

The goal is to verify that the configured overlap is applied consistently and that short or boundary-sized inputs do not generate unnecessary chunks or non-terminating behavior.

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

## Test Fixture

Controlled overlap cases are defined in:

`tests/fixtures/overlap_cases.json`

The fixture includes:

- text shorter than the chunk size
- text exactly equal to the chunk size
- text slightly larger than the chunk size
- longer text producing multiple chunks

## Test File

Automated tests:

`tests/test_chunk_overlap.py`

The test suite verifies:

- consecutive chunks contain the declared 200-character overlap
- short text produces only one chunk
- exact-boundary text produces only one chunk
- slightly oversized text terminates cleanly with two chunks
- long text produces a finite and reasonable number of chunks

## Overlap Verification

For consecutive chunks, the final 200 characters of the current chunk are compared with the first 200 characters of the following chunk.

The expected relationship is:

```text
current_chunk[-200:] == next_chunk[:200]
```

This confirms that the configured overlap is reflected in the generated chunk sequence.

## Boundary Behavior

### Short Input

A 600-character input produces one chunk.

No unnecessary overlap chunk is generated.

### Exact Chunk Boundary

A 1000-character input produces one chunk.

No second chunk is created solely because overlap is configured.

### Slightly Over Boundary

An 1100-character input produces two chunks and terminates normally.

The expected overlap is present between the two chunks.

### Longer Input

A 2600-character input produces multiple chunks while maintaining the configured overlap.

The operation terminates normally and does not produce an unbounded sequence.

## Test Execution

Command:

```bash
python -m pytest tests/test_chunk_overlap.py -v
```

Observed result:

```text
5 passed
```

## Repeated Execution

The same test suite was executed again without changing the fixture or implementation.

Observed result:

```text
5 passed
```

The repeated execution produced the same passing behavior.

## Result

The observed chunk overlap is consistent with the declared configuration:

```text
chunk_overlap = 200
```

Boundary inputs do not generate unnecessary chunks, and the tested inputs terminate normally.

## Conclusion

T14 confirms that Docu AI's current chunk overlap behavior is consistent with its declared configuration.

The tests also establish that short and boundary-sized inputs do not create unnecessary chunks or indicate non-terminating splitting behavior.