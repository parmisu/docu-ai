# Deduplication Policy Report

## Purpose

This report documents the deduplication behavior used in Docu AI and verifies that duplicate removal does not destroy required source or page information.

The goal is to distinguish between:

- true duplicate content
- identical text appearing on different pages
- identical text appearing in different source documents

## Deduplication Policy

Docu AI uses a conservative deduplication policy.

A document is considered a duplicate only when all three values are identical:

```text
page_content
source
page
```

In other words, the deduplication key is:

```python
(
    document.page_content,
    document.metadata.get("source"),
    document.metadata.get("page"),
)
```

This prevents identical text from being removed when it comes from a different page or a different source document.

## Implementation

The deduplication helper is implemented in:

`deduplication.py`

The helper preserves the first occurrence of an exact duplicate and removes later occurrences with the same:

- text
- source
- page number

Original document order is preserved.

## Test Fixture

Controlled test cases are stored in:

`tests/fixtures/deduplication_cases.json`

The fixture covers:

- exact duplicate content on the same page
- identical text on different pages of the same document
- identical text from different source documents
- mixed duplicate and non-duplicate content

## Test File

Automated tests are implemented in:

`tests/test_deduplication.py`

The tests verify that:

- exact duplicates from the same source and page are removed
- identical text from different pages is preserved
- identical text from different source documents is preserved
- required source and page metadata remains available
- original ordering of unique content is preserved

## Exact Duplicate Behavior

Example:

```text
Text: Repeated content from page one.
Source: document_a.pdf
Page: 1
```

If the exact same record appears more than once, only one copy is retained.

This is treated as a true duplicate.

## Same Text on Different Pages

Example:

```text
Text: Shared paragraph text.
Source: document_a.pdf
Page: 1
```

and:

```text
Text: Shared paragraph text.
Source: document_a.pdf
Page: 2
```

Both records are preserved.

Although the text is identical, the page metadata represents different source locations.

Removing either record would lose valid provenance information.

## Same Text from Different Sources

Example:

```text
Text: Identical content appears here.
Source: document_a.pdf
Page: 1
```

and:

```text
Text: Identical content appears here.
Source: document_b.pdf
Page: 1
```

Both records are preserved.

Identical text from separate documents is not considered an exact duplicate because the source metadata differs.

## Metadata Preservation

The deduplication process does not remove required provenance information.

For retained records, the following metadata remains intact:

- source document
- page number

This allows later retrieval results to remain traceable to the correct document location.

## Order Preservation

Deduplication keeps the first valid occurrence of each exact record.

The relative order of non-duplicate documents is preserved.

This avoids introducing content reordering during duplicate removal.

## Test Execution

Command:

```bash
python -m pytest tests/test_deduplication.py -v
```

Observed result:

```text
5 passed
```

## Repeated Execution

The test suite was executed again without modifying the fixture or implementation.

Observed result:

```text
5 passed
```

The repeated execution produced the same behavior.

## Result

The tested deduplication policy removes only exact duplicate records.

Identical text is preserved when it belongs to:

- a different page
- a different source document

Source and page metadata remain available for all retained content.

## Conclusion

T17 confirms that Docu AI uses a provenance-aware deduplication policy.

Duplicate removal is based on text, source, and page together rather than text alone.

This prevents valid content from being incorrectly removed and preserves the metadata required for later retrieval and citation.