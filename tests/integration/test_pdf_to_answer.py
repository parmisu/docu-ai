import json
import os
from pathlib import Path
from uuid import uuid4

import pytest
from pypdf import PdfReader

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.messages import HumanMessage
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter


ROOT = Path(__file__).parent.parent.parent

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
    / "integration-results.jsonl"
)

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

QUESTION = (
    "What sensor network does "
    "the Aurora research project use?"
)

EXPECTED_ANSWER_TERMS = [
    "cobalt-blue",
]

EXPECTED_CITATION_TEXT = (
    "cobalt-blue sensor network"
)

EXPECTED_SOURCE = "document_a.pdf"
EXPECTED_PAGE = 1


class DeterministicEmbeddings(
    Embeddings
):
    def embed_documents(
        self,
        texts,
    ):
        return [
            self._vector(text)
            for text in texts
        ]

    def embed_query(
        self,
        text,
    ):
        return self._vector(text)

    @staticmethod
    def _vector(text):
        normalized = text.lower()

        terms = [
            "aurora",
            "sensor",
            "cobalt",
            "blue",
            "network",
        ]

        return [
            float(
                normalized.count(term)
            )
            for term in terms
        ]


class SimulatedAnswerModel:
    def invoke(
        self,
        messages,
    ):
        prompt = messages[0].content

        if (
            EXPECTED_CITATION_TEXT
            in prompt
        ):
            return type(
                "Response",
                (),
                {
                    "content": (
                        "The Aurora research project "
                        "uses a cobalt-blue sensor network."
                    )
                },
            )()

        return type(
            "Response",
            (),
            {
                "content": (
                    "ANSWER CANNOT BE FOUND "
                    "IN THE PROVIDED DOCUMENT."
                )
            },
        )()


def extract_pdf(
    pdf_path,
):
    reader = PdfReader(
        pdf_path
    )

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
                        "source": (
                            pdf_path.name
                        ),
                        "page": (
                            page_number
                        ),
                    },
                )
            )

    return documents


def chunk_documents(
    documents,
):
    splitter = (
        RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=(
                CHUNK_OVERLAP
            ),
        )
    )

    return splitter.split_documents(
        documents
    )


def build_store(
    chunks,
    embeddings,
):
    return Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=(
            f"integration_"
            f"{uuid4().hex}"
        ),
    )


def retrieve(
    store,
):
    return (
        store
        .similarity_search_with_relevance_scores(
            QUESTION,
            k=3,
        )
    )


def build_context(
    results,
):
    parts = []

    for rank, (
        document,
        score,
    ) in enumerate(
        results,
        start=1,
    ):
        parts.append(
            (
                f"[Result {rank}]\n"
                f"Source: "
                f"{document.metadata['source']}\n"
                f"Page: "
                f"{document.metadata['page']}\n"
                f"Content: "
                f"{document.page_content}"
            )
        )

    return "\n\n".join(
        parts
    )


def generate_answer(
    model,
    results,
):
    context = build_context(
        results
    )

    prompt = f"""
Use only the supplied document context.

If the answer is supported by the context,
answer directly.

If the answer cannot be found, respond:
ANSWER CANNOT BE FOUND IN THE PROVIDED DOCUMENT.

Context:
{context}

Question:
{QUESTION}

Answer:
"""

    response = model.invoke(
        [
            HumanMessage(
                content=prompt
            )
        ]
    )

    return (
        response.content.strip(),
        prompt,
    )


def citation_is_correct(
    results,
):
    for document, _ in results:
        if (
            document.metadata[
                "source"
            ]
            == EXPECTED_SOURCE
            and document.metadata[
                "page"
            ]
            == EXPECTED_PAGE
            and EXPECTED_CITATION_TEXT
            in document.page_content
        ):
            return True

    return False


def answer_is_correct(
    answer,
):
    normalized_answer = (
        answer.lower()
    )

    return all(
        term.lower()
        in normalized_answer
        for term in EXPECTED_ANSWER_TERMS
    )


def write_result(
    record,
):
    RESULTS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    existing = []

    if RESULTS_PATH.exists():
        with RESULTS_PATH.open(
            "r",
            encoding="utf-8",
        ) as file:
            for line in file:
                line = line.strip()

                if line:
                    existing.append(
                        json.loads(
                            line
                        )
                    )

    existing = [
        item
        for item in existing
        if item["mode"]
        != record["mode"]
    ]

    existing.append(
        record
    )

    with RESULTS_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        for item in existing:
            file.write(
                json.dumps(
                    item,
                    ensure_ascii=False,
                )
                + "\n"
            )


def run_pipeline(
    model,
    embeddings,
    mode,
):
    documents = extract_pdf(
        PDF_PATH
    )

    assert len(documents) > 0

    chunks = chunk_documents(
        documents
    )

    assert len(chunks) > 0

    store = build_store(
        chunks,
        embeddings,
    )

    results = retrieve(
        store
    )

    assert len(results) > 0

    answer, prompt = (
        generate_answer(
            model,
            results,
        )
    )

    answer_correct = (
        answer_is_correct(
            answer
        )
    )

    citation_correct = (
        citation_is_correct(
            results
        )
    )

    record = {
        "mode": mode,
        "pdf": PDF_PATH.name,
        "question": QUESTION,
        "expected_answer_terms": (
            EXPECTED_ANSWER_TERMS
        ),
        "expected_citation_text": (
            EXPECTED_CITATION_TEXT
        ),
        "model_answer": answer,
        "answer_correct": (
            answer_correct
        ),
        "citation_correct": (
            citation_correct
        ),
        "retrieved_sources": [
            {
                "source": (
                    document.metadata[
                        "source"
                    ]
                ),
                "page": (
                    document.metadata[
                        "page"
                    ]
                ),
                "score": round(
                    float(score),
                    6,
                ),
            }
            for document, score
            in results
        ],
        "prompt": prompt,
        "overall_pass": (
            answer_correct
            and citation_correct
        ),
    }

    write_result(
        record
    )

    return record


def test_simulated_pdf_to_answer_pipeline():
    record = run_pipeline(
        model=(
            SimulatedAnswerModel()
        ),
        embeddings=(
            DeterministicEmbeddings()
        ),
        mode="simulated",
    )

    assert (
        record[
            "answer_correct"
        ]
        is True
    )

    assert (
        record[
            "citation_correct"
        ]
        is True
    )

    assert (
        record[
            "overall_pass"
        ]
        is True
    )


@pytest.mark.integration
def test_real_ollama_pdf_to_answer_pipeline():
    if (
        os.getenv(
            "RUN_OLLAMA_TESTS"
        )
        != "1"
    ):
        pytest.skip(
            "requires real Ollama; "
            "run with RUN_OLLAMA_TESTS=1"
        )

    model = ChatOllama(
        model="llama3.2:3b",
        temperature=0,
    )

    embeddings = (
        HuggingFaceEmbeddings(
            model_name=(
                "sentence-transformers/"
                "all-MiniLM-L6-v2"
            )
        )
    )

    record = run_pipeline(
        model=model,
        embeddings=embeddings,
        mode="real_ollama",
    )

    assert (
        record[
            "answer_correct"
        ]
        is True
    )

    assert (
        record[
            "citation_correct"
        ]
        is True
    )

    assert (
        record[
            "overall_pass"
        ]
        is True
    )