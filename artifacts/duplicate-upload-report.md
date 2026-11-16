# Duplicate Upload Behavior Report

## Purpose

This report evaluates Docu AI's behavior when the exact same PDF is uploaded repeatedly.

The test verifies whether repeated uploads create duplicate vector-store records or unnecessarily recompute document embeddings.

## Duplicate Upload Policy

Docu AI identifies an uploaded document using a SHA-256 hash of its file bytes.

The expected behavior is:

```text
same PDF bytes
→ same document key
→ existing cached vector store reused
→ no duplicate records added
→ document embeddings not recomputed
```

A repeated upload is therefore treated as the same document rather than as a new indexing operation.

## Test Document

The controlled fixture is:

```text
tests/fixtures/pdf/document_a.pdf
```

The same PDF is processed three times during the test.

## Test File

Automated tests are implemented in:

```text
tests/test_duplicate_upload.py
```

The test suite verifies:

- identical PDF bytes produce the same SHA-256 document key
- the first upload creates the vector store
- subsequent uploads produce cache hits
- stored record count does not increase on duplicate uploads
- document embeddings are computed during the initial indexing operation
- document embeddings are not recomputed for later duplicate uploads

## Measurement Strategy

A controlled embedding implementation records:

```text
document embedding calls
number of documents embedded
```

This allows the test to distinguish between an actual embedding operation and a cache reuse.

The vector store is also inspected after each upload to measure the number of stored records.

## Expected Sequence

### Upload 1

The first upload is not present in cache.

Expected behavior:

```text
cache hit = false
embedding operation = performed
vector records = initial chunk count
```

### Upload 2

The same PDF is uploaded again.

Because the file bytes are identical, its SHA-256 document key is unchanged.

Expected behavior:

```text
cache hit = true
embedding operation = not repeated
vector records = unchanged
```

### Upload 3

The same document is uploaded once more.

Expected behavior remains:

```text
cache hit = true
embedding operation = not repeated
vector records = unchanged
```

## Duplicate Record Check

The number of stored vector records is compared with the original input chunk count after every upload.

Repeated uploads must not cause behavior such as:

```text
initial count
→ 2 × initial count
→ 3 × initial count
```

Instead, the record count must remain equal to the original chunk count.

## Embedding Reuse Check

The initial upload performs one document-embedding operation.

The second and third uploads perform zero new document-embedding operations.

This confirms that the cached vector store prevents unnecessary re-indexing of an identical PDF.

## Results

The automated test suite completed successfully:

```text
3 passed
```

Detailed measurements are stored in:

```text
evaluation/duplicate-upload-results.csv
```

The results show that repeated uploads reuse the existing cached vector store rather than appending duplicate records.

Document embeddings are also not recomputed after the initial upload.

## Conclusion

T24 confirms that Docu AI has an explicit duplicate-upload policy based on PDF content identity.

When the same PDF is uploaded repeatedly:

- the SHA-256 document key remains unchanged
- the existing vector store is reused
- stored record count remains stable
- duplicate chunks are not appended
- document embeddings are not unnecessarily recomputed

This avoids redundant processing and prevents duplicate vector records from accumulating during repeated uploads.