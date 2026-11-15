from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "expected_text"
    / "order_case.txt"
)

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def load_source_text() -> str:
    return FIXTURE_PATH.read_text(
        encoding="utf-8"
    ).strip()


def split_source_text():
    text = load_source_text()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    document = Document(
        page_content=text,
        metadata={
            "source": "order_case",
            "page": 1,
        },
    )

    return splitter.split_documents(
        [document]
    )


def extract_markers(text: str) -> list[str]:
    markers = []

    for token in text.split():
        if token.startswith("PARAGRAPH_"):
            markers.append(token)

    return markers


def test_original_marker_order_is_preserved():
    source_text = load_source_text()

    expected_markers = extract_markers(
        source_text
    )

    chunks = split_source_text()

    observed_markers = []

    for chunk in chunks:
        for marker in extract_markers(
            chunk.page_content
        ):
            if (
                not observed_markers
                or marker != observed_markers[-1]
            ):
                observed_markers.append(marker)

    assert observed_markers == expected_markers


def test_each_original_marker_remains_present():
    source_text = load_source_text()

    expected_markers = set(
        extract_markers(source_text)
    )

    chunks = split_source_text()

    combined = "\n".join(
        chunk.page_content
        for chunk in chunks
    )

    for marker in expected_markers:
        assert marker in combined


def test_overlap_does_not_reverse_content_order():
    chunks = split_source_text()

    first_occurrence = {}

    for chunk_index, chunk in enumerate(chunks):
        for marker in extract_markers(
            chunk.page_content
        ):
            first_occurrence.setdefault(
                marker,
                chunk_index,
            )

    ordered_markers = extract_markers(
        load_source_text()
    )

    observed_positions = [
        first_occurrence[marker]
        for marker in ordered_markers
    ]

    assert observed_positions == sorted(
        observed_positions
    )


def test_chunk_metadata_is_preserved():
    chunks = split_source_text()

    for chunk in chunks:
        assert chunk.metadata["source"] == (
            "order_case"
        )
        assert chunk.metadata["page"] == 1