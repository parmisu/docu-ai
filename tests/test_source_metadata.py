import json
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "expected_text"
    / "source_metadata.json"
)

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def load_fixture():
    return json.loads(
        FIXTURE_PATH.read_text(
            encoding="utf-8"
        )
    )


def build_page_documents():
    fixture = load_fixture()

    documents = []

    for page_data in fixture["pages"]:
        documents.append(
            Document(
                page_content=page_data["text"],
                metadata={
                    "source": fixture["source"],
                    "page": page_data["page"],
                },
            )
        )

    return documents


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    return splitter.split_documents(documents)


def get_test_embeddings():
    return HuggingFaceEmbeddings(
        model_name=(
            "sentence-transformers/"
            "all-MiniLM-L6-v2"
        )
    )


def build_vector_store(chunks):
    return Chroma.from_documents(
        documents=chunks,
        embedding=get_test_embeddings(),
        collection_name="source_metadata_test",
    )


def test_page_numbering_contract_is_one_based():
    fixture = load_fixture()

    assert fixture["page_numbering"] == (
        "one-based"
    )

    pages = [
        page["page"]
        for page in fixture["pages"]
    ]

    assert pages == [1, 2, 3]


def test_metadata_survives_chunking():
    documents = build_page_documents()
    chunks = split_documents(documents)

    assert len(chunks) == 3

    for chunk, expected_page in zip(
        chunks,
        [1, 2, 3],
    ):
        assert (
            chunk.metadata["source"]
            == "source_metadata_fixture.pdf"
        )

        assert (
            chunk.metadata["page"]
            == expected_page
        )


def test_vector_store_retrieval_preserves_source_metadata():
    documents = build_page_documents()
    chunks = split_documents(documents)

    vector_store = build_vector_store(
        chunks
    )

    results = vector_store.similarity_search(
        "Which page discusses ChromaDB?",
        k=1,
    )

    assert len(results) == 1

    result = results[0]

    assert (
        result.metadata["source"]
        == "source_metadata_fixture.pdf"
    )

    assert result.metadata["page"] == 2

    assert (
        "PAGE_TWO_MARKER"
        in result.page_content
    )


def test_each_retrieved_page_matches_real_source_page():
    documents = build_page_documents()
    chunks = split_documents(documents)

    vector_store = build_vector_store(
        chunks
    )

    queries = [
        (
            "Python document processing pipeline",
            1,
            "PAGE_ONE_MARKER",
        ),
        (
            "ChromaDB vector embeddings",
            2,
            "PAGE_TWO_MARKER",
        ),
        (
            "Ollama local language model",
            3,
            "PAGE_THREE_MARKER",
        ),
    ]

    for query, expected_page, marker in queries:
        results = (
            vector_store.similarity_search(
                query,
                k=1,
            )
        )

        assert len(results) == 1

        result = results[0]

        assert (
            result.metadata["source"]
            == "source_metadata_fixture.pdf"
        )

        assert (
            result.metadata["page"]
            == expected_page
        )

        assert marker in result.page_content