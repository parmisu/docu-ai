# Vector Store Persistence Test Report

## Purpose

This report evaluates whether Docu AI's Chroma vector store survives a full application restart.

The goal is to determine whether vector data is persisted across processes or rebuilt during each new application run.

## Current Storage Design

Docu AI currently creates its Chroma vector store without a configured persistent storage directory.

No `persist_directory` is defined in the application.

The current design is therefore:

```text
PDF upload
→ text extraction
→ chunking
→ embedding
→ in-memory Chroma vector store
```

The vector store exists for the lifetime of the active application process.

## Test Method

The persistence test is implemented in:

```text
tests/test_vector_store_persistence.py
```

The test uses separate Python processes to simulate an application shutdown and restart.

This is important because creating two vector-store objects inside the same process would not accurately represent a real restart.

## First Process

The first process:

1. creates a Chroma collection
2. stores a controlled document record
3. verifies that the stored record exists

Observed record count:

```text
1
```

The process then terminates.

## Second Process

A new Python process is started using the same collection name.

Because no persistent Chroma directory is configured, the new process does not recover the vector records created by the previous process.

Observed record count:

```text
0
```

## Application Configuration Check

The test also inspects the current application source and confirms that no configuration of the following form is present:

```python
persist_directory=...
```

This matches the observed restart behavior.

## Runtime Cache vs Persistent Storage

Docu AI currently distinguishes between runtime caching and durable persistence.

Within the same application runtime:

```text
same PDF
→ same SHA-256 document key
→ cached vector store may be reused
```

This behavior is covered by the duplicate-upload tests.

Across a complete application restart:

```text
application exits
→ in-memory vector store is lost
→ application starts again
→ PDF must be processed again
→ embeddings are recomputed
→ vector store is rebuilt
```

The runtime cache therefore improves repeated-document behavior during one session but does not provide cross-session persistence.

## Test Execution

Command:

```bash
python -m pytest tests/test_vector_store_persistence.py -v
```

Observed result:

```text
3 passed
```

## Result

The controlled restart test confirms that Docu AI's current vector store is:

```text
non-persistent
```

or equivalently:

```text
runtime-scoped
```

Vector records created during one process are not automatically available to a new process.

## Design Consistency

The observed behavior matches the current architecture.

Docu AI does not currently claim durable Chroma persistence and does not configure a persistent storage directory.

Rebuilding the vector store after an application restart is therefore expected behavior rather than an unexpected storage failure.

## Limitation

For large documents, rebuilding the vector store after every fresh application start may require additional processing time and repeated embedding computation.

This is a known limitation of the current local-first architecture.

## Future Improvement

If cross-session reuse becomes a requirement, a future implementation could use an explicit persistent Chroma directory and define lifecycle rules for:

- document replacement
- deletion
- duplicate uploads
- cache invalidation
- persisted collection cleanup

Such a change would require additional persistence and lifecycle tests.

## Conclusion

T26 confirms that Docu AI currently uses a runtime-scoped, non-persistent vector store.

The vector store may be reused during the same application runtime, but a complete restart causes the indexed data to be lost and rebuilt.

This behavior is consistent with the documented architecture.