import time
from pathlib import Path

from pypdf import PdfReader


PDF_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "pdf"
    / "large_sample.pdf"
)

EXPECTED_PAGE_COUNT = 50

MAX_EXTRACTION_SECONDS = 10.0


def test_large_pdf_page_count():
    reader = PdfReader(PDF_PATH)

    assert len(reader.pages) == (
        EXPECTED_PAGE_COUNT
    )


def test_large_pdf_text_extraction_performance():
    start_time = time.perf_counter()

    reader = PdfReader(PDF_PATH)

    extracted_pages = [
        page.extract_text() or ""
        for page in reader.pages
    ]

    elapsed = (
        time.perf_counter()
        - start_time
    )

    assert len(extracted_pages) == (
        EXPECTED_PAGE_COUNT
    )

    assert all(
        text.strip()
        for text in extracted_pages
    )

    assert elapsed < (
        MAX_EXTRACTION_SECONDS
    ), (
        "Large PDF extraction exceeded "
        f"{MAX_EXTRACTION_SECONDS}s: "
        f"{elapsed:.3f}s"
    )


def test_large_pdf_preserves_page_markers():
    reader = PdfReader(PDF_PATH)

    for page_number, page in enumerate(
        reader.pages,
        start=1,
    ):
        text = page.extract_text() or ""

        expected_marker = (
            f"DOCU-AI-PAGE-"
            f"{page_number:03d}"
        )

        assert expected_marker in text