# Corrupted PDF Handling Report

## Purpose

This report documents how Docu AI handles corrupted or unreadable PDF files.

The goal is to verify that invalid PDF input does not leave the application in an unhealthy processing state and that the user receives a clear error message.

## Test Fixture

Corrupted PDF fixture:

`tests/fixtures/pdf/corrupted.pdf`

The fixture is intentionally malformed and cannot be parsed as a valid PDF.

## Test File

Automated tests:

`tests/test_corrupted_pdf.py`

The tests verify that:

- the corrupted file cannot be opened as a valid PDF
- PyPDF raises `PdfReadError`
- the corrupted file does not produce usable pages

## Application Error Handling

The PDF processing path now wraps both PDF opening and page extraction in error handling.

If the PDF cannot be opened, the application displays:

```text
This PDF could not be opened. The file may be corrupted, incomplete, or not a valid PDF.
```

If page extraction fails after the PDF has been opened, the application displays:

```text
The PDF could not be read correctly. One or more pages may be corrupted or incomplete.
```

In both cases, processing stops immediately with `st.stop()`.

This prevents the application from continuing to chunking, embedding, retrieval, or answer generation using invalid document state.

## Test Execution

Command:

```bash
python -m pytest tests/test_corrupted_pdf.py -v
```

Observed result:

```text
2 passed in 0.09s
```

## Result

The corrupted PDF fixture was rejected as expected.

No valid reader state or page content was produced.

The application now contains explicit failure handling for both:

- PDF opening errors
- page extraction errors

## Recovery Behavior

A failed PDF load does not continue into the normal RAG pipeline.

The application stops processing and can recover through the next Streamlit rerun when the user provides a different file.

## Conclusion

Docu AI now fails safely when it receives a corrupted or incomplete PDF instead of allowing invalid document state to continue through the pipeline.

This test does not yet cover:

- password-protected PDFs
- encrypted PDFs
- partially damaged PDFs that still open
- filesystem or permission errors
- model/runtime failures unrelated to PDF parsing