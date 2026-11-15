import json
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "chunking_cases.json"
)

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def load_cases():
    data = json.loads(
        FIXTURE_PATH.read_text(encoding="utf-8")
    )

    assert data["chunk_size"] == CHUNK_SIZE
    assert data["chunk_overlap"] == CHUNK_OVERLAP

    return data["cases"]


def make_text(length: int) -> str:
    return "A" * length


def make_splitter():
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )


def split_text(text: str):
    document = Document(
        page_content=text,
        metadata={
            "source": "chunking_fixture",
            "page": 1,
        },
    )

    return make_splitter().split_documents(
        [document]
    )


def test_chunking_boundary_cases():
    for case in load_cases():
        text = make_text(case["length"])
        chunks = split_text(text)

        assert chunks, (
            f"No chunks created for case: {case['name']}"
        )

        assert all(
            chunk.page_content
            for chunk in chunks
        )


def test_short_text_stays_in_single_chunk():
    text = make_text(600)

    chunks = split_text(text)

    assert len(chunks) == 1
    assert chunks[0].page_content == text


def test_exact_chunk_size_stays_in_single_chunk():
    text = make_text(CHUNK_SIZE)

    chunks = split_text(text)

    assert len(chunks) == 1
    assert chunks[0].page_content == text


def test_slightly_over_chunk_size_splits():
    text = make_text(1100)

    chunks = split_text(text)

    assert len(chunks) >= 2


def test_very_long_text_produces_multiple_chunks():
    text = make_text(5000)

    chunks = split_text(text)

    assert len(chunks) > 2


def test_no_non_empty_content_is_lost():
    text = (
        "START_MARKER "
        + ("A" * 1800)
        + " MIDDLE_MARKER "
        + ("B" * 1800)
        + " END_MARKER"
    )

    chunks = split_text(text)

    combined = "\n".join(
        chunk.page_content
        for chunk in chunks
    )

    assert "START_MARKER" in combined
    assert "MIDDLE_MARKER" in combined
    assert "END_MARKER" in combined


def test_metadata_is_preserved():
    text = make_text(1100)

    chunks = split_text(text)

    for chunk in chunks:
        assert chunk.metadata["source"] == (
            "chunking_fixture"
        )
        assert chunk.metadata["page"] == 1