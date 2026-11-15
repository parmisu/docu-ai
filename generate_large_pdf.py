from pathlib import Path


OUTPUT_PATH = Path(
    "tests/fixtures/pdf/large_sample.pdf"
)

PAGE_COUNT = 50


def build_page_content(page_number: int) -> str:
    lines = [
        f"Docu AI Large PDF Performance Fixture - Page {page_number}",
        (
            "This page contains controlled text used for "
            "performance and extraction testing."
        ),
        (
            "The document is intentionally repetitive so "
            "performance measurements remain reproducible."
        ),
        (
            f"Unique page marker: DOCU-AI-PAGE-{page_number:03d}"
        ),
    ]

    content = "BT\n/F1 12 Tf\n72 720 Td\n"

    for index, line in enumerate(lines):
        safe = (
            line.replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
        )

        if index == 0:
            content += f"({safe}) Tj\n"
        else:
            content += (
                f"0 -22 Td\n({safe}) Tj\n"
            )

    content += "ET\n"

    return content


objects = []

objects.append(
    "1 0 obj\n"
    "<< /Type /Catalog /Pages 2 0 R >>\n"
    "endobj\n"
)

page_object_numbers = [
    3 + index * 2
    for index in range(PAGE_COUNT)
]

kids = " ".join(
    f"{number} 0 R"
    for number in page_object_numbers
)

objects.append(
    "2 0 obj\n"
    f"<< /Type /Pages /Kids [{kids}] "
    f"/Count {PAGE_COUNT} >>\n"
    "endobj\n"
)

font_object_number = (
    3 + PAGE_COUNT * 2
)

for index in range(PAGE_COUNT):
    page_number = index + 1

    page_object = 3 + index * 2
    content_object = page_object + 1

    content = build_page_content(
        page_number
    )

    objects.append(
        f"{page_object} 0 obj\n"
        "<< /Type /Page "
        "/Parent 2 0 R "
        "/MediaBox [0 0 612 792] "
        "/Resources << /Font "
        f"<< /F1 {font_object_number} 0 R >> "
        ">> "
        f"/Contents {content_object} 0 R >>\n"
        "endobj\n"
    )

    objects.append(
        f"{content_object} 0 obj\n"
        f"<< /Length "
        f"{len(content.encode('latin-1'))} >>\n"
        "stream\n"
        f"{content}"
        "endstream\n"
        "endobj\n"
    )

objects.append(
    f"{font_object_number} 0 obj\n"
    "<< /Type /Font "
    "/Subtype /Type1 "
    "/BaseFont /Helvetica >>\n"
    "endobj\n"
)

pdf = bytearray(b"%PDF-1.4\n")
offsets = [0]

for obj in objects:
    offsets.append(len(pdf))
    pdf.extend(
        obj.encode("latin-1")
    )

xref_offset = len(pdf)

pdf.extend(
    f"xref\n0 {len(objects) + 1}\n".encode()
)
pdf.extend(
    b"0000000000 65535 f \n"
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

OUTPUT_PATH.write_bytes(pdf)

print(
    f"Created {OUTPUT_PATH} "
    f"with {PAGE_COUNT} pages."
)