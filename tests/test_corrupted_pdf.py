from pathlib import Path

import pytest
from pypdf import PdfReader
from pypdf.errors import PdfReadError


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "pdf"

CORRUPTED_PDF = FIXTURES_DIR / "corrupted.pdf"


def test_corrupted_pdf_cannot_be_opened():
    with pytest.raises(PdfReadError):
        PdfReader(CORRUPTED_PDF)


def test_corrupted_pdf_does_not_produce_pages():
    try:
        reader = PdfReader(CORRUPTED_PDF)
    except PdfReadError:
        reader = None

    assert reader is None