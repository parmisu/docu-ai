from pathlib import Path

from pypdf import PdfReader


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "pdf"

EMPTY_PDF = FIXTURES_DIR / "empty.pdf"
IMAGE_ONLY_PDF = FIXTURES_DIR / "image_only.pdf"


def extract_non_empty_pages(pdf_path: Path) -> list[str]:
    reader = PdfReader(pdf_path)

    extracted_pages = []

    for page in reader.pages:
        text = page.extract_text() or ""

        if text.strip():
            extracted_pages.append(text)

    return extracted_pages


def test_empty_pdf_has_no_extractable_text():
    extracted_pages = extract_non_empty_pages(EMPTY_PDF)

    assert extracted_pages == []


def test_image_only_pdf_has_no_extractable_text_without_ocr():
    extracted_pages = extract_non_empty_pages(IMAGE_ONLY_PDF)

    assert extracted_pages == []