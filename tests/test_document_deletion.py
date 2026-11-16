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


PDF_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "pdf"
    / "document_a.pdf"
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


def build_store():
    return Chroma.from_documents(
        documents=extract_documents(
            PDF_PATH
        ),
        embedding=get_embeddings(),
        collection_name=(
            f"deletion_{uuid4().hex}"
        ),
    )


def test_delete_clears_active_document():
    lifecycle = DocumentLifecycle()

    lifecycle.register(
        document_hash(PDF_PATH),
        build_store(),
    )

    assert lifecycle.active_key is not None
    assert (
        lifecycle.get_active_store()
        is not None
    )

    lifecycle.delete_active()

    assert lifecycle.active_key is None
    assert (
        lifecycle.get_active_store()
        is None
    )


def test_deleted_document_cannot_be_searched():
    lifecycle = DocumentLifecycle()

    lifecycle.register(
        document_hash(PDF_PATH),
        build_store(),
    )

    before_delete = (
        lifecycle.search_active(
            "What sensor network does "
            "the Aurora project use?",
            k=1,
        )
    )

    assert len(before_delete) == 1

    assert (
        "DOCUMENT_A_MARKER"
        in before_delete[0].page_content
    )

    lifecycle.delete_active()

    after_delete = (
        lifecycle.search_active(
            "What sensor network does "
            "the Aurora project use?",
            k=1,
        )
    )

    assert after_delete == []


def test_delete_does_not_reactivate_previous_store():
    lifecycle = DocumentLifecycle()

    lifecycle.register(
        document_hash(PDF_PATH),
        build_store(),
    )

    lifecycle.delete_active()

    first_search = lifecycle.search_active(
        "Aurora",
        k=1,
    )

    second_search = lifecycle.search_active(
        "cobalt-blue sensor network",
        k=1,
    )

    assert first_search == []
    assert second_search == []