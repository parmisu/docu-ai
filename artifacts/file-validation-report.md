# File Validation Test Report

## Purpose

This report documents validation behavior for files that are not valid PDF documents.

The goal is to ensure that Docu AI does not trust a file solely because its filename ends in `.pdf`.

## Validation Strategy

The application now performs two levels of validation:

1. The Streamlit uploader limits normal selection to `.pdf` files.
2. The application checks the uploaded file content for a PDF signature before passing it to PyPDF.

The signature check is implemented in:

`pdf_validation.py`

using:

```python
has_pdf_signature(file_obj)
```

The validator checks for a `%PDF-` signature near the beginning of the file and restores the original file position after validation.

## Test Fixture

Non-PDF fixture:

`tests/fixtures/pdf/not_a_pdf.txt`

The fixture contains ordinary plain text and no valid PDF signature.

## Test File

Automated tests:

`tests/test_file_validation.py`

The tests verify that:

- a plain text file is rejected
- a fake `.pdf` filename is not sufficient for acceptance
- a file containing a PDF signature is accepted by the signature check
- validation does not change the file object's original read position

## Application Behavior

If the uploaded file does not contain a valid PDF signature, the application displays:

```text
The uploaded file is not a valid PDF. Please upload a genuine PDF document.
```

Processing stops before `PdfReader`, chunking, embedding, retrieval, or answer generation.

Parser-level validation remains active after the signature check, so malformed files that contain a PDF-like signature can still be rejected by PyPDF.

## Test Execution

Command:

```bash
python -m pytest tests/test_file_validation.py -v
```

Observed result:

```text
4 passed in 0.01s
```

## Repeated Execution

The same command was executed again without changing the fixtures or validation code.

Observed result:

```text
4 passed in 0.01s
```

The repeated execution produced the same passing result.

## Result

The validation layer rejects files based on their content rather than trusting the filename extension alone.

A renamed text file with a `.pdf` filename is therefore not considered a valid PDF.

## Conclusion

Docu AI now performs content-based validation before attempting normal PDF processing.

This reduces the chance that invalid or misleading input reaches the document-processing pipeline.

The signature check is intentionally lightweight and is not a replacement for parser-level validation. PyPDF remains responsible for validating the actual PDF structure.