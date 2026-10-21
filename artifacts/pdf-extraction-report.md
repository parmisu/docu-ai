# PDF Extraction Test Report

## Purpose

This report records the first automated PDF extraction test added to Docu AI.

The goal was to verify that text can be extracted from a known single-page PDF and compared against a known reference while ignoring harmless whitespace differences.

## Test Fixture

PDF fixture:

`tests/fixtures/pdf/single_page.pdf`

Expected text fixture:

`tests/fixtures/expected_text/single_page.txt`

The PDF contains known text created specifically for deterministic extraction testing.

## Test File

Automated test:

`tests/test_pdf_extraction.py`

The test verifies:

- the PDF contains exactly one page
- text extraction succeeds
- extracted text contains the expected content
- harmless differences in spaces and line breaks do not cause failure

## Normalization

Before comparison, whitespace is normalized using a regular expression.

This converts repeated whitespace and line breaks into a consistent single-space representation.

## First Execution

Command:

```bash
python -m pytest tests/test_pdf_extraction.py -v
```

Observed result:

```text
1 passed in 0.05s
```