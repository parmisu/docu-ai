from pathlib import Path


OUTPUT_DIR = Path(
    "tests/fixtures/pdf"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


def write_simple_pdf(path, text):
    objects = []

    objects.append(
        b"<< /Type /Catalog /Pages 2 0 R >>"
    )

    objects.append(
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>"
    )

    objects.append(
        (
            b"<< /Type /Page "
            b"/Parent 2 0 R "
            b"/MediaBox [0 0 612 792] "
            b"/Resources << "
            b"/Font << /F1 4 0 R >> "
            b">> "
            b"/Contents 5 0 R >>"
        )
    )

    objects.append(
        (
            b"<< /Type /Font "
            b"/Subtype /Type1 "
            b"/BaseFont /Helvetica >>"
        )
    )

    safe_text = (
        text
        .replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )

    stream = (
        "BT\n"
        "/F1 14 Tf\n"
        "72 720 Td\n"
        f"({safe_text}) Tj\n"
        "ET\n"
    ).encode("latin-1")

    objects.append(
        (
            f"<< /Length {len(stream)} >>\n"
            "stream\n"
        ).encode("ascii")
        + stream
        + b"endstream"
    )

    pdf = bytearray(
        b"%PDF-1.4\n"
    )

    offsets = [0]

    for index, obj in enumerate(
        objects,
        start=1,
    ):
        offsets.append(len(pdf))

        pdf.extend(
            f"{index} 0 obj\n".encode()
        )

        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)

    pdf.extend(
        (
            f"xref\n"
            f"0 {len(objects) + 1}\n"
            f"0000000000 65535 f \n"
        ).encode()
    )

    for offset in offsets[1:]:
        pdf.extend(
            f"{offset:010d} 00000 n \n".encode()
        )

    pdf.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} "
            "/Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF\n"
        ).encode()
    )

    path.write_bytes(pdf)


write_simple_pdf(
    OUTPUT_DIR / "document_a.pdf",
    (
        "DOCUMENT_A_MARKER "
        "The Aurora research project uses "
        "a cobalt-blue sensor network."
    ),
)

write_simple_pdf(
    OUTPUT_DIR / "document_b.pdf",
    (
        "DOCUMENT_B_MARKER "
        "The Beacon research project uses "
        "a solar-powered tracking system."
    ),
)

print(
    "Created document_a.pdf and document_b.pdf"
)