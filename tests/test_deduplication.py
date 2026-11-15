import json
from pathlib import Path

from langchain_core.documents import Document

from deduplication import deduplicate_documents


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "deduplication_cases.json"
)


def load_fixture():
    return json.loads(
        FIXTURE_PATH.read_text(
            encoding="utf-8"
        )
    )


def build_documents(case):
    return [
        Document(
            page_content=item["text"],
            metadata={
                "source": item["source"],
                "page": item["page"],
            },
        )
        for item in case["documents"]
    ]


def get_case(name):
    fixture = load_fixture()

    return next(
        case
        for case in fixture["cases"]
        if case["name"] == name
    )


def test_exact_duplicate_same_page_is_removed():
    case = get_case(
        "exact_duplicate_same_page"
    )

    documents = build_documents(case)
    result = deduplicate_documents(
        documents
    )

    assert len(result) == (
        case["expected_count"]
    )

    assert result[0].metadata == {
        "source": "document_a.pdf",
        "page": 1,
    }


def test_same_text_on_different_pages_is_preserved():
    case = get_case(
        "same_text_different_pages"
    )

    documents = build_documents(case)
    result = deduplicate_documents(
        documents
    )

    assert len(result) == (
        case["expected_count"]
    )

    assert [
        document.metadata["page"]
        for document in result
    ] == [1, 2]


def test_same_text_from_different_sources_is_preserved():
    case = get_case(
        "same_text_different_sources"
    )

    documents = build_documents(case)
    result = deduplicate_documents(
        documents
    )

    assert len(result) == (
        case["expected_count"]
    )

    assert {
        document.metadata["source"]
        for document in result
    } == {
        "document_a.pdf",
        "document_b.pdf",
    }


def test_mixed_duplicates_preserve_required_metadata():
    case = get_case(
        "mixed_duplicates"
    )

    documents = build_documents(case)
    result = deduplicate_documents(
        documents
    )

    assert len(result) == (
        case["expected_count"]
    )

    preserved_locations = {
        (
            document.metadata["source"],
            document.metadata["page"],
        )
        for document in result
    }

    assert preserved_locations == {
        ("document_a.pdf", 1),
        ("document_a.pdf", 2),
        ("document_b.pdf", 1),
    }


def test_deduplication_preserves_original_order():
    case = get_case(
        "mixed_duplicates"
    )

    documents = build_documents(case)
    result = deduplicate_documents(
        documents
    )

    assert [
        (
            document.metadata["source"],
            document.metadata["page"],
        )
        for document in result
    ] == [
        ("document_a.pdf", 1),
        ("document_a.pdf", 2),
        ("document_b.pdf", 1),
    ]