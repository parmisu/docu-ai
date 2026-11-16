import hashlib
from pathlib import Path
from uuid import uuid4

from pypdf import PdfReader

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import (
    HuggingFaceEmbeddings,
)

from document_lifecycle import (
    DocumentLifecycle,
)


FIXTURE_DIR = (
    Path(__file__).parent
    / "fixtures"
    / "pdf"
)

DOCUMENT_A = (
    FIXTURE_DIR
    / "document_a.pdf"
)

DOCUMENT_B = (
    FIXTURE_DIR
    / "document_b.pdf"
)


def document_hash(path):
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def extract_documents(path):
    reader = PdfReader(path)

    documents = []

    for page_number, page in enumerate(
        reader.pages,
        start=1,
    ):
        text = (
            page.extract_text() or ""
        ).strip()

        if text:
            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": path.name,
                        "page": page_number,
                    },
                )
            )

    return documents


def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=(
            "sentence-transformers/"
            "all-MiniLM-L6-v2"
        )
    )


def build_store(path):
    return Chroma.from_documents(
        documents=extract_documents(path),
        embedding=get_embeddings(),
        collection_name=(
            f"replacement_{uuid4().hex}"
        ),
    )


def test_replacement_changes_active_document():
    lifecycle = DocumentLifecycle()

    key_a = document_hash(DOCUMENT_A)
    store_a = build_store(DOCUMENT_A)

    lifecycle.register(
        key_a,
        store_a,
    )

    assert lifecycle.active_key == key_a

    key_b = document_hash(DOCUMENT_B)
    store_b = build_store(DOCUMENT_B)

    lifecycle.replace(
        key_b,
        store_b,
    )

    assert lifecycle.active_key == key_b
    assert lifecycle.get_active_store() is store_b
    assert lifecycle.get_active_store() is not store_a


def test_old_document_is_not_retrievable_after_replacement():
    lifecycle = DocumentLifecycle()

    lifecycle.register(
        document_hash(DOCUMENT_A),
        build_store(DOCUMENT_A),
    )

    results_a = lifecycle.search_active(
        "What sensor network does "
        "the Aurora project use?",
        k=1,
    )

    assert (
        "DOCUMENT_A_MARKER"
        in results_a[0].page_content
    )

    lifecycle.replace(
        document_hash(DOCUMENT_B),
        build_store(DOCUMENT_B),
    )

    old_question_results = (
        lifecycle.search_active(
            "What sensor network does "
            "the Aurora project use?",
            k=1,
        )
    )

    assert len(old_question_results) == 1

    assert (
        "DOCUMENT_A_MARKER"
        not in old_question_results[
            0
        ].page_content
    )

    assert (
        old_question_results[
            0
        ].metadata["source"]
        == "document_b.pdf"
    )


def test_new_document_is_retrievable_after_replacement():
    lifecycle = DocumentLifecycle()

    lifecycle.register(
        document_hash(DOCUMENT_A),
        build_store(DOCUMENT_A),
    )

    lifecycle.replace(
        document_hash(DOCUMENT_B),
        build_store(DOCUMENT_B),
    )

    results = lifecycle.search_active(
        "What tracking system does "
        "the Beacon project use?",
        k=1,
    )

    assert (
        "DOCUMENT_B_MARKER"
        in results[0].page_content
    )

    assert (
        "DOCUMENT_A_MARKER"
        not in results[0].page_content
    )