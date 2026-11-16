# Document Lifecycle Report

## Purpose

This report verifies Docu AI's behavior when an active document is replaced or deleted.

The goal is to ensure that information from a previously active document is not available through the current search path after replacement or deletion.

## Lifecycle Policy

Docu AI uses an explicit active-document model.

The policy is:

```text
REGISTER
→ document becomes active

REPLACE
→ new document becomes active
→ previous document is no longer searchable through the active path

DELETE
→ no document remains active
→ active search returns no results
```

A previous vector store may remain cached internally for reuse, but cached data is not considered active data.

Only the vector store associated with the current active document may be searched.

## Lifecycle Helper

Lifecycle behavior is implemented in:

```text
document_lifecycle.py
```

The helper tracks:

```text
active document key
registered vector stores
active search path
```

The active document is identified by its document key.

## Replacement Test

Automated replacement tests are implemented in:

```text
tests/test_document_replacement.py
```

Two controlled PDFs are used:

```text
tests/fixtures/pdf/document_a.pdf
tests/fixtures/pdf/document_b.pdf
```

Document A contains:

```text
DOCUMENT_A_MARKER
```

Document B contains:

```text
DOCUMENT_B_MARKER
```

## Replacement Sequence

The controlled sequence is:

```text
register A
→ search A
→ replace A with B
→ search B
→ ask an A-specific question while B is active
```

Before replacement, an A-specific question returns content containing:

```text
DOCUMENT_A_MARKER
```

After replacement, the active key changes to document B.

The active vector store is therefore B's store.

An A-specific query executed after replacement may still return the nearest available B chunk because similarity search returns a nearest result, but that result must not contain A's content.

The returned source must identify:

```text
document_b.pdf
```

## Replacement Result

After document B replaces document A:

- B becomes the active document
- B-specific information remains retrievable
- A's unique marker is not returned through active search
- A's source metadata is not returned through active search

This confirms that the previous document is no longer available through the active retrieval path.

## Deletion Test

Automated deletion tests are implemented in:

```text
tests/test_document_deletion.py
```

The deletion sequence is:

```text
register document A
→ verify A can be searched
→ delete active document
→ attempt A-specific search
```

Before deletion, A-specific retrieval succeeds.

After deletion:

```text
active_key = None
```

and:

```text
get_active_store() = None
```

## Search Behavior After Deletion

After the active document is deleted, searches return:

```text
[]
```

Repeated attempts to search for old document information also return no active results.

Deletion therefore does not silently reactivate the previous vector store.

## Cached Data vs Active Data

The lifecycle policy distinguishes between:

```text
cached store
```

and:

```text
active searchable store
```

A store may remain cached internally for performance reasons.

However, cached records are not reachable through `search_active()` unless their document key is currently active.

This prevents old document content from leaking into the active retrieval context.

## Test Execution

Command:

```bash
python -m pytest tests/test_document_replacement.py tests/test_document_deletion.py -v
```

Observed result:

```text
6 passed
```

## Result

The controlled lifecycle tests confirm that:

- replacing A with B switches the active retrieval context to B
- old A content is not returned through the active search path
- deleting the active document clears the active key
- no active vector store remains after deletion
- attempts to retrieve deleted content return no active search results
- previously cached stores are not automatically reactivated

## Conclusion

T25 establishes an explicit document lifecycle policy for Docu AI.

Replacement changes the active search context to the new document, while deletion removes the active search context entirely.

Old document information therefore remains inaccessible through the active retrieval path after either replacement or deletion.