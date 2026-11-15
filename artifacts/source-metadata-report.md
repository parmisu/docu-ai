# Source Metadata Traceability Report

## Purpose

This report verifies that source metadata remains attached to document content throughout the Docu AI retrieval pipeline.

The tested path is:

```text
page document
→ chunking
→ vector storage
→ similarity retrieval
```

The goal is to confirm that each retrieved result can be traced back to the correct source document and the correct page.

## Page Numbering Convention

Docu AI uses **one-based page numbering** in document metadata.

This means:

- first page = `1`
- second page = `2`
- third page = `3`

The controlled fixture explicitly defines this convention.

## Test Fixture

Controlled metadata is stored in:

`tests/fixtures/expected_text/source_metadata.json`

The fixture defines:

- source document name
- expected page number
- unique text marker for each page
- explicit page-numbering convention

The controlled source name is:

```text
source_metadata_fixture.pdf
```

## Test File

Automated tests are implemented in:

`tests/test_source_metadata.py`

The tests verify:

- the page-numbering contract is one-based
- source and page metadata survive chunking
- source metadata survives vector-store insertion and retrieval
- retrieved content corresponds to the expected real source page

## Metadata During Chunking

Each page is represented as a LangChain `Document` containing metadata such as:

```python
{
    "source": "source_metadata_fixture.pdf",
    "page": 2
}
```

After the document is split into chunks, the tests confirm that the metadata remains attached to the resulting chunk.

## Metadata During Retrieval

The controlled chunks are inserted into a Chroma vector store using the same Hugging Face embedding model used by Docu AI:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Similarity queries are then executed against the vector store.

For each retrieved result, the tests verify:

- the source file name
- the page number
- the unique page marker contained in the retrieved text

For example, a query about ChromaDB is expected to retrieve:

```text
source = source_metadata_fixture.pdf
page = 2
marker = PAGE_TWO_MARKER
```

This links the retrieval result directly to its controlled source page.

## End-to-End Traceability

The metadata path tested is:

```text
source page
→ Document metadata
→ chunk metadata
→ Chroma storage
→ retrieved Document metadata
```

The retrieved metadata matched the expected document and page values for the controlled cases.

## Test Execution

Command:

```bash
python -m pytest tests/test_source_metadata.py -v
```

Observed result:

```text
4 passed
```

## Repeated Execution

The test suite was executed again without changing the fixture or implementation.

Observed result:

```text
4 passed
```

The repeated execution produced the same passing behavior.

## Result

The controlled retrieval results remained correctly associated with:

- the original source document
- the expected source page
- the expected page content marker

The page-numbering convention is explicitly defined as one-based.

## Conclusion

T16 confirms that source and page metadata remain traceable through chunking, vector storage, and retrieval for the controlled test cases.

Each retrieved result can therefore be linked back to the correct document and page under the current metadata contract.