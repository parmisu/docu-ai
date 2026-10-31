from io import BytesIO
from pathlib import Path

from pdf_validation import has_pdf_signature


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "pdf"

NOT_A_PDF = FIXTURES_DIR / "not_a_pdf.txt"


def test_plain_text_file_is_rejected():
    with NOT_A_PDF.open("rb") as file_obj:
        assert has_pdf_signature(file_obj) is False


def test_fake_pdf_extension_is_not_enough():
    fake_pdf = BytesIO(
        b"This file has a .pdf name but contains plain text."
    )

    assert has_pdf_signature(fake_pdf) is False


def test_real_pdf_signature_is_accepted():
    valid_pdf = BytesIO(
        b"%PDF-1.4\n"
        b"minimal test content"
    )

    assert has_pdf_signature(valid_pdf) is True


def test_validation_preserves_file_position():
    file_obj = BytesIO(
        b"%PDF-1.4\n"
        b"test"
    )

    file_obj.seek(3)

    has_pdf_signature(file_obj)

    assert file_obj.tell() == 3