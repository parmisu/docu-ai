import json
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "overlap_cases.json"
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
    pattern = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    repeats = (length // len(pattern)) + 1

    return (pattern * repeats)[:length]


def split_text(text: str):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    document = Document(
        page_content=text,
        metadata={
            "source": "overlap_fixture",
            "page": 1,
        },
    )

    return splitter.split_documents(
        [document]
    )


def test_declared_overlap_between_consecutive_chunks():
    text = make_text(2600)

    chunks = split_text(text)

    assert len(chunks) >= 3

    for current, following in zip(
        chunks,
        chunks[1:],
    ):
        assert (
            current.page_content[-CHUNK_OVERLAP:]
            == following.page_content[:CHUNK_OVERLAP]
        )


def test_short_text_does_not_create_extra_chunks():
    text = make_text(600)

    chunks = split_text(text)

    assert len(chunks) == 1
    assert chunks[0].page_content == text


def test_exact_boundary_does_not_create_extra_chunks():
    text = make_text(CHUNK_SIZE)

    chunks = split_text(text)

    assert len(chunks) == 1
    assert chunks[0].page_content == text


def test_slightly_over_boundary_terminates_cleanly():
    text = make_text(1100)

    chunks = split_text(text)

    assert len(chunks) == 2

    assert (
        chunks[0].page_content[-CHUNK_OVERLAP:]
        == chunks[1].page_content[:CHUNK_OVERLAP]
    )


def test_all_overlap_cases_produce_reasonable_chunk_counts():
    for case in load_cases():
        text = make_text(case["length"])
        chunks = split_text(text)

        assert len(chunks) > 0

        if "expected_chunks" in case:
            assert len(chunks) == case["expected_chunks"]

        if "expected_min_chunks" in case:
            assert (
                len(chunks)
                >= case["expected_min_chunks"]
            )