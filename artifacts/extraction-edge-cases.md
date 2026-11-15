# Extraction Edge Cases Report

## Purpose

This report documents how Docu AI handles irregular text extraction output, including unusual whitespace, line breaks, incomplete text, and Unicode replacement characters.

The goal is to normalize harmless formatting differences without removing meaningful document content.

## Test Fixture

Expected cleaning cases are stored in:

`tests/fixtures/expected_text/edge_cases.json`

The fixture includes controlled examples for:

- multiple spaces
- tab characters
- irregular line breaks
- surrounding whitespace
- Unicode replacement characters
- punctuation preservation

## Test File

Automated tests:

`tests/test_extraction_edge_cases.py`

The test suite verifies that:

- harmless whitespace is normalized
- tabs are converted into normal spacing
- excessive blank lines are reduced without removing paragraph boundaries
- surrounding whitespace is removed
- replacement characters are handled conservatively
- punctuation and essential technical terms are preserved

## Cleaning Implementation

Text cleaning is implemented in:

`text_cleaning.py`

using:

```python
clean_extracted_text(text)
```

The function performs conservative normalization rather than aggressive rewriting.

Current behavior includes:

- replacing Unicode replacement characters with whitespace
- collapsing repeated spaces and tabs
- removing spaces around line breaks
- limiting excessive consecutive line breaks
- preserving meaningful words and punctuation

## Initial Test Failure

The first test execution exposed an issue in the line-break normalization logic.

The original implementation used:

```python
re.sub(r"\s*\n\s*", "\n", cleaned)
```

Because `\s` also matches newline characters, this expression collapsed more line breaks than intended and removed paragraph boundaries.

The `irregular_line_breaks` case failed.

## Fix

The normalization logic was changed to:

```python
re.sub(r"[ \t]*\n[ \t]*", "\n", cleaned)
```

This limits the rule to spaces and tabs around newlines instead of matching newlines themselves.

Excessive line breaks are then handled separately with:

```python
re.sub(r"\n{3,}", "\n\n", cleaned)
```

This preserves intentional paragraph separation.

## Test Execution

Command:

```bash
python -m pytest tests/test_extraction_edge_cases.py -v
```

Observed result after the fix:

```text
2 passed
```

## Repeated Execution

The same test command was executed again without changing the fixture or implementation.

Observed result:

```text
2 passed
```

The repeated execution produced the same passing result.

## Content Preservation

The test suite explicitly checks that essential terms remain present after cleaning, including:

- `Python 3.11`
- `ChromaDB`
- `Ollama`
- `Streamlit`

The cleaning layer is intentionally conservative and does not remove content solely because it appears unusual.

## Result

The extraction-cleaning logic now handles the tested whitespace and replacement-character edge cases consistently while preserving essential content.

## Conclusion

T11 identified and corrected a real normalization bug.

The final implementation avoids over-cleaning extracted text and preserves paragraph boundaries and important technical content.