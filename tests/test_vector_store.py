import json
from pathlib import Path

import pytest
from uuid import uuid4

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "vector_store_cases.json"
)


def load_fixture():
    return json.loads(
        FIXTURE_PATH.read_text(
            encoding="utf-8"
        )
    )


def build_documents():
    fixture = load_fixture()

    return [
        Document(
            page_content=item["text"],
            metadata={
                "source": item["source"],
                "page": item["page"],
            },
        )
        for item in fixture["documents"]
    ]


def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=(
            "sentence-transformers/"
            "all-MiniLM-L6-v2"
        )
    )


def build_empty_vector_store():
    return Chroma(
        collection_name=f"vector_store_test_{uuid4().hex}",
        embedding_function=get_embeddings(),
    )


def test_input_chunk_count_matches_fixture():
    documents = build_documents()

    assert len(documents) == 4


def test_vector_store_returns_one_id_per_chunk():
    documents = build_documents()
    vector_store = build_empty_vector_store()

    ids = vector_store.add_documents(
        documents
    )

    assert len(ids) == len(documents)

    assert all(ids)

    assert len(set(ids)) == len(ids)


def test_stored_record_count_matches_input_count():
    documents = build_documents()
    vector_store = build_empty_vector_store()

    vector_store.add_documents(
        documents
    )

    stored = vector_store.get()

    assert len(stored["ids"]) == (
        len(documents)
    )

    assert len(stored["documents"]) == (
        len(documents)
    )

    assert len(stored["metadatas"]) == (
        len(documents)
    )


def test_stored_content_and_metadata_are_preserved():
    documents = build_documents()
    vector_store = build_empty_vector_store()

    vector_store.add_documents(
        documents
    )

    stored = vector_store.get()

    stored_records = {
        document_text: metadata
        for document_text, metadata in zip(
            stored["documents"],
            stored["metadatas"],
        )
    }

    for original in documents:
        assert (
            original.page_content
            in stored_records
        )

        metadata = stored_records[
            original.page_content
        ]

        assert (
            metadata["source"]
            == original.metadata["source"]
        )

        assert (
            metadata["page"]
            == original.metadata["page"]
        )


def test_stored_ids_are_unique():
    documents = build_documents()
    vector_store = build_empty_vector_store()

    vector_store.add_documents(
        documents
    )

    stored = vector_store.get()

    ids = stored["ids"]

    assert len(ids) == len(set(ids))


def test_storage_error_is_not_silently_ignored(
    monkeypatch,
):
    documents = build_documents()
    vector_store = build_empty_vector_store()

    def fail_add(*args, **kwargs):
        raise RuntimeError(
            "Simulated vector storage failure"
        )

    monkeypatch.setattr(
        vector_store,
        "add_documents",
        fail_add,
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated vector storage failure",
    ):
        vector_store.add_documents(
            documents
        )