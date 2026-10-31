def has_pdf_signature(file_obj) -> bool:
    """Check whether a file contains a PDF signature near its beginning."""

    original_position = file_obj.tell()

    try:
        file_obj.seek(0)
        header = file_obj.read(1024)

        return b"%PDF-" in header

    finally:
        file_obj.seek(original_position)