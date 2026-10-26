import json
import re
from pathlib import Path

from pypdf import PdfReader


FIXTURES_DIR = Path(__file__).parent / "fixtures"

PDF_PATH = FIXTURES_DIR / "pdf" / "multi_page.pdf"

EXPECTED_PATH = (
    FIXTURES_DIR
    / "expected_text"
    / "multi_page.json"
)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def test_multi_page_pdf_preserves_page_order_and_boundaries():
    reader = PdfReader(PDF_PATH)

    expected = json.loads(
        EXPECTED_PATH.read_text(encoding="utf-8")
    )

    expected_pages = expected["pages"]

    assert len(reader.pages) == len(expected_pages)

    extracted_pages = []

    for page_number, page in enumerate(
        reader.pages,
        start=1,
    ):
        text = page.extract_text() or ""

        extracted_pages.append(
            {
                "page": page_number,
                "text": normalize_text(text),
            }
        )

    for extracted, expected_page in zip(
        extracted_pages,
        expected_pages,
    ):
        assert extracted["page"] == expected_page["page"]

        assert extracted["text"] == normalize_text(
            expected_page["text"]
        )


def test_page_numbers_remain_traceable():
    reader = PdfReader(PDF_PATH)

    page_records = [
        {
            "page": page_number,
            "text": normalize_text(
                page.extract_text() or ""
            ),
        }
        for page_number, page in enumerate(
            reader.pages,
            start=1,
        )
    ]

    assert [record["page"] for record in page_records] == [
        1,
        2,
        3,
    ]