# Document Isolation and Cache Replacement Report

## Purpose

This report verifies that replacing one uploaded PDF with another does not allow content from the previous document to remain available through the active vector store.

The test specifically covers the document replacement path and cache identity.

The required sequence is:

```text
load document A
→ build/cache vector store A
→ query document A
→ replace with document B
→ build/cache vector store B
→ query document B
→ query for information unique to A
```

The expected behavior is that information from document A is not treated as present in document B.

## Test Fixtures

Two controlled PDF fixtures are used:

```text
tests/fixtures/pdf/document_a.pdf
tests/fixtures/pdf/document_b.pdf
```

### Document A

Contains the unique marker:

```text
DOCUMENT_A_MARKER
```

and the controlled fact:

```text
The Aurora research project uses a cobalt-blue sensor network.
```

### Document B

Contains the unique marker:

```text
DOCUMENT_B_MARKER
```

and the controlled fact:

```text
The Beacon research project uses a solar-powered tracking system.
```

The two documents therefore contain deliberately distinct information.

## Cache-Key Strategy

The uploaded PDF bytes are hashed using SHA-256.

Example:

```python
uploaded_bytes = uploaded_file.getvalue()

document_key = hashlib.sha256(
    uploaded_bytes
).hexdigest()
```

The vector-store cache function receives this key:

```python
get_vector_store(
    document_key,
    chunks,
)
```

This ensures that two different PDF files produce different cache identities.

Document A and document B therefore do not share the same cached vector store.

## Why This Change Was Required

Previously, the vector-store cache function accepted the document collection through an underscore-prefixed argument.

Streamlit excludes underscore-prefixed parameters from cache hashing.

This created a risk that replacing one PDF with another could reuse the vector store created for the previous document.

The document hash is now explicitly included in the cache key.

## Test File

The automated isolation tests are implemented in:

```text
tests/test_vector_store_isolation.py
```

The test suite verifies that:

- document A and B produce different SHA-256 hashes
- both PDF fixtures contain their expected unique markers
- replacing A with B creates a different vector-store instance
- retrieval against A returns A-specific information
- retrieval against B returns B-specific information
- B's stored content does not contain A's marker
- B's stored content does not contain A's unique fact
- asking an A-specific question against B does not return A content
- returned metadata identifies document B after replacement

## Replacement Sequence

The test first loads document A.

Its extracted content is chunked and stored using the hash of A as the cache key.

An A-specific question is then queried and the returned result must contain:

```text
DOCUMENT_A_MARKER
```

The test then loads document B.

Because document B has different file bytes, it generates a different SHA-256 cache key.

A new vector store is created for B.

The B-specific query must return:

```text
DOCUMENT_B_MARKER
```

and must not contain:

```text
DOCUMENT_A_MARKER
```

## Old-Document Leakage Check

After replacing A with B, the contents of the active B vector store are inspected directly.

The stored B collection must contain:

```text
DOCUMENT_B_MARKER
```

and must not contain:

```text
DOCUMENT_A_MARKER
```

or:

```text
cobalt-blue sensor network
```

This verifies that information from the old document has not leaked into the active replacement store.

## Cross-Document Question Check

An A-specific question is intentionally asked against the B store.

The retrieval system may still return the nearest B chunk because vector search always attempts to find a closest result.

However, the returned content must:

- not contain A's unique marker
- not contain A's unique fact
- identify its source as `document_b.pdf`

This distinguishes retrieval behavior from actual evidence that A's information remains available.

## Test Execution

Command:

```bash
python -m pytest tests/test_vector_store_isolation.py -v
```

Observed result:

```text
5 passed
```

## Result

The controlled document replacement workflow successfully isolates document A from document B.

After document B replaces document A:

- B receives a distinct cache key
- B uses a separate vector store
- B-specific retrieval works
- A-specific content is absent from B's stored records
- A-specific information is not returned as if it were present in B

## Conclusion

T23 confirms that document replacement is now tied to the uploaded PDF content through a SHA-256 cache key.

This prevents stale vector-store reuse when the user replaces one PDF with another and ensures that the active retrieval context belongs to the current document.