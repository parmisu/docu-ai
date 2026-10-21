import re
from pathlib import Path

from pypdf import PdfReader


FIXTURES_DIR = Path(__file__).parent / "fixtures"

PDF_PATH = FIXTURES_DIR / "pdf" / "single_page.pdf"

EXPECTED_TEXT_PATH = (
    FIXTURES_DIR
    / "expected_text"
    / "single_page.txt"
)


def normalize_text(text: str) -> str:
    """Normalize harmless whitespace differences."""
    return re.sub(r"\s+", " ", text).strip()


def test_single_page_pdf_extraction_matches_expected_text():
    reader = PdfReader(PDF_PATH)

    assert len(reader.pages) == 1

    extracted_text = reader.pages[0].extract_text() or ""

    expected_text = EXPECTED_TEXT_PATH.read_text(
        encoding="utf-8"
    )

    assert normalize_text(extracted_text) == normalize_text(
        expected_text
    )