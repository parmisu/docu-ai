import csv
import hashlib
from pathlib import Path
from uuid import uuid4

from pypdf import PdfReader

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


ROOT = Path(__file__).parent.parent

PDF_PATH = (
    ROOT
    / "tests"
    / "fixtures"
    / "pdf"
    / "document_a.pdf"
)

RESULTS_PATH = (
    ROOT
    / "evaluation"
    / "duplicate-upload-results.csv"
)

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


class CountingEmbeddings(Embeddings):
    def __init__(self):
        self.document_embedding_calls = 0
        self.documents_embedded = 0

    def embed_documents(self, texts):
        self.document_embedding_calls += 1
        self.documents_embedded += len(texts)

        return [
            self._vector(text)
            for text in texts
        ]

    def embed_query(self, text):
        return self._vector(text)

    @staticmethod
    def _vector(text):
        value = float(
            sum(ord(char) for char in text) % 1000
        ) / 1000.0

        return [
            value,
            value / 2.0,
            1.0 - value,
        ]


class DuplicateUploadCache:
    def __init__(self, embeddings):
        self.embeddings = embeddings
        self.cache = {}

    def get_vector_store(
        self,
        document_key,
        chunks,
    ):
        cache_hit = document_key in self.cache

        if not cache_hit:
            self.cache[document_key] = (
                Chroma.from_documents(
                    documents=chunks,
                    embedding=self.embeddings,
                    collection_name=(
                        "duplicate_upload_"
                        f"{uuid4().hex}"
                    ),
                )
            )

        return (
            self.cache[document_key],
            cache_hit,
        )


def document_hash(path):
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def extract_and_chunk(path):
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

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    return splitter.split_documents(
        documents
    )


def run_duplicate_upload_sequence():
    embeddings = CountingEmbeddings()

    cache = DuplicateUploadCache(
        embeddings
    )

    rows = []

    document_key = document_hash(
        PDF_PATH
    )

    expected_chunks = extract_and_chunk(
        PDF_PATH
    )

    for upload_number in range(1, 4):
        chunks = extract_and_chunk(
            PDF_PATH
        )

        calls_before = (
            embeddings.document_embedding_calls
        )

        embedded_before = (
            embeddings.documents_embedded
        )

        store, cache_hit = (
            cache.get_vector_store(
                document_key,
                chunks,
            )
        )

        calls_after = (
            embeddings.document_embedding_calls
        )

        embedded_after = (
            embeddings.documents_embedded
        )

        stored = store.get()

        rows.append(
            {
                "upload_number": upload_number,
                "document_key": document_key,
                "input_chunk_count": len(chunks),
                "stored_record_count": len(
                    stored["ids"]
                ),
                "cache_hit": cache_hit,
                "embedding_calls_this_upload": (
                    calls_after - calls_before
                ),
                "documents_embedded_this_upload": (
                    embedded_after
                    - embedded_before
                ),
            }
        )

    return (
        rows,
        len(expected_chunks),
        embeddings,
    )


def write_results(rows):
    RESULTS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with RESULTS_PATH.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "upload_number",
                "document_key",
                "input_chunk_count",
                "stored_record_count",
                "cache_hit",
                "embedding_calls_this_upload",
                "documents_embedded_this_upload",
            ],
        )

        writer.writeheader()
        writer.writerows(rows)


def test_same_pdf_produces_same_document_key():
    first_key = document_hash(
        PDF_PATH
    )

    second_key = document_hash(
        PDF_PATH
    )

    assert first_key == second_key


def test_duplicate_upload_reuses_store_without_duplicate_records():
    rows, expected_chunk_count, _ = (
        run_duplicate_upload_sequence()
    )

    write_results(rows)

    assert rows[0]["cache_hit"] is False
    assert rows[1]["cache_hit"] is True
    assert rows[2]["cache_hit"] is True

    for row in rows:
        assert (
            row["input_chunk_count"]
            == expected_chunk_count
        )

        assert (
            row["stored_record_count"]
            == expected_chunk_count
        )


def test_embeddings_are_not_recomputed_for_duplicate_upload():
    rows, expected_chunk_count, embeddings = (
        run_duplicate_upload_sequence()
    )

    write_results(rows)

    assert (
        rows[0]["embedding_calls_this_upload"]
        == 1
    )

    assert (
        rows[0]["documents_embedded_this_upload"]
        == expected_chunk_count
    )

    assert (
        rows[1]["embedding_calls_this_upload"]
        == 0
    )

    assert (
        rows[2]["embedding_calls_this_upload"]
        == 0
    )

    assert (
        rows[1]["documents_embedded_this_upload"]
        == 0
    )

    assert (
        rows[2]["documents_embedded_this_upload"]
        == 0
    )

    assert (
        embeddings.document_embedding_calls
        == 1
    )

    assert (
        embeddings.documents_embedded
        == expected_chunk_count
    )