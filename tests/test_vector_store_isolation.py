import hashlib
from pathlib import Path
from uuid import uuid4

from pypdf import PdfReader

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


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

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def document_hash(path):
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def extract_documents(path):
    reader = PdfReader(path)

    page_documents = []

    for page_number, page in enumerate(
        reader.pages,
        start=1,
    ):
        text = (
            page.extract_text() or ""
        ).strip()

        if text:
            page_documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": path.name,
                        "page": page_number,
                    },
                )
            )

    return page_documents


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    return splitter.split_documents(
        documents
    )


def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=(
            "sentence-transformers/"
            "all-MiniLM-L6-v2"
        )
    )


class CachedVectorStore:
    def __init__(self):
        self.cache = {}

    def get_vector_store(
        self,
        document_key,
        documents,
    ):
        if document_key not in self.cache:
            self.cache[document_key] = (
                Chroma.from_documents(
                    documents=documents,
                    embedding=get_embeddings(),
                    collection_name=(
                        f"isolation_{uuid4().hex}"
                    ),
                )
            )

        return self.cache[document_key]


def load_document(path):
    documents = extract_documents(path)
    chunks = split_documents(documents)

    return (
        document_hash(path),
        chunks,
    )


def test_fixture_documents_are_unique():
    key_a, chunks_a = load_document(
        DOCUMENT_A
    )

    key_b, chunks_b = load_document(
        DOCUMENT_B
    )

    assert key_a != key_b

    assert any(
        "DOCUMENT_A_MARKER"
        in chunk.page_content
        for chunk in chunks_a
    )

    assert any(
        "DOCUMENT_B_MARKER"
        in chunk.page_content
        for chunk in chunks_b
    )


def test_replacing_document_changes_cache_key():
    key_a, _ = load_document(
        DOCUMENT_A
    )

    key_b, _ = load_document(
        DOCUMENT_B
    )

    assert key_a != key_b


def test_document_b_retrieval_does_not_return_a():
    cache = CachedVectorStore()

    key_a, chunks_a = load_document(
        DOCUMENT_A
    )

    store_a = cache.get_vector_store(
        key_a,
        chunks_a,
    )

    results_a = store_a.similarity_search(
        "What sensor network does "
        "the Aurora project use?",
        k=1,
    )

    assert (
        "DOCUMENT_A_MARKER"
        in results_a[0].page_content
    )

    key_b, chunks_b = load_document(
        DOCUMENT_B
    )

    store_b = cache.get_vector_store(
        key_b,
        chunks_b,
    )

    assert store_b is not store_a

    results_b = store_b.similarity_search(
        "What tracking system does "
        "the Beacon project use?",
        k=1,
    )

    assert (
        "DOCUMENT_B_MARKER"
        in results_b[0].page_content
    )

    assert (
        "DOCUMENT_A_MARKER"
        not in results_b[0].page_content
    )


def test_old_document_information_is_not_present_after_replacement():
    cache = CachedVectorStore()

    key_a, chunks_a = load_document(
        DOCUMENT_A
    )

    cache.get_vector_store(
        key_a,
        chunks_a,
    )

    key_b, chunks_b = load_document(
        DOCUMENT_B
    )

    store_b = cache.get_vector_store(
        key_b,
        chunks_b,
    )

    stored_b = store_b.get()

    combined_b = " ".join(
        stored_b["documents"]
    )

    assert (
        "DOCUMENT_B_MARKER"
        in combined_b
    )

    assert (
        "DOCUMENT_A_MARKER"
        not in combined_b
    )

    assert (
        "cobalt-blue sensor network"
        not in combined_b
    )


def test_question_about_a_is_not_supported_by_b_store():
    cache = CachedVectorStore()

    key_a, chunks_a = load_document(
        DOCUMENT_A
    )

    cache.get_vector_store(
        key_a,
        chunks_a,
    )

    key_b, chunks_b = load_document(
        DOCUMENT_B
    )

    store_b = cache.get_vector_store(
        key_b,
        chunks_b,
    )

    results = store_b.similarity_search(
        "What sensor network does "
        "the Aurora project use?",
        k=1,
    )

    assert len(results) == 1

    assert (
        "DOCUMENT_A_MARKER"
        not in results[0].page_content
    )

    assert (
        results[0].metadata["source"]
        == "document_b.pdf"
    )