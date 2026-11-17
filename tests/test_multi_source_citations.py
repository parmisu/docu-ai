import csv
import json
from pathlib import Path
from uuid import uuid4

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings


ROOT = Path(__file__).parent.parent

FIXTURE_PATH = (
    ROOT
    / "tests"
    / "fixtures"
    / "multi_source_cases.json"
)

RESULTS_PATH = (
    ROOT
    / "evaluation"
    / "multi-source-results.csv"
)

TOP_K = 5


def load_fixture():
    return json.loads(
        FIXTURE_PATH.read_text(
            encoding="utf-8"
        )
    )


def normalize(text):
    return " ".join(
        text.lower().split()
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


def build_vector_store():
    return Chroma.from_documents(
        documents=build_documents(),
        embedding=get_embeddings(),
        collection_name=(
            f"multi_source_test_{uuid4().hex}"
        ),
    )


def evidence_supports_claim(
    text,
    required_terms,
):
    normalized_text = normalize(text)

    return all(
        normalize(term)
        in normalized_text
        for term in required_terms
    )


def find_supporting_citation(
    results,
    claim,
):
    for rank, (
        document,
        score,
    ) in enumerate(
        results,
        start=1,
    ):
        source_matches = (
            document.metadata["source"]
            == claim["expected_source"]
        )

        page_matches = (
            document.metadata["page"]
            == claim["expected_page"]
        )

        evidence_matches = (
            evidence_supports_claim(
                document.page_content,
                claim["required_terms"],
            )
        )

        if (
            source_matches
            and page_matches
            and evidence_matches
        ):
            return (
                rank,
                document,
                score,
            )

    return None, None, None


def write_results(rows):
    RESULTS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with RESULTS_PATH.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "case_id",
                "question",
                "claim",
                "expected_source",
                "expected_page",
                "status",
                "citation_rank",
                "actual_source",
                "actual_page",
                "evidence_supports_claim",
                "score",
            ],
        )

        writer.writeheader()
        writer.writerows(rows)


def test_each_claim_has_supporting_citation():
    fixture = load_fixture()
    vector_store = build_vector_store()

    rows = []
    failures = []

    for case in fixture["cases"]:
        results = (
            vector_store
            .similarity_search_with_relevance_scores(
                case["question"],
                k=TOP_K,
            )
        )

        assert len(results) > 0

        for claim in case["claims"]:
            rank, document, score = (
                find_supporting_citation(
                    results,
                    claim,
                )
            )

            found = document is not None

            rows.append(
                {
                    "case_id": case["id"],
                    "question": (
                        case["question"]
                    ),
                    "claim": claim["claim"],
                    "expected_source": (
                        claim[
                            "expected_source"
                        ]
                    ),
                    "expected_page": (
                        claim[
                            "expected_page"
                        ]
                    ),
                    "status": (
                        "FOUND"
                        if found
                        else "MISSING"
                    ),
                    "citation_rank": (
                        rank
                        if rank is not None
                        else ""
                    ),
                    "actual_source": (
                        document.metadata[
                            "source"
                        ]
                        if document
                        else ""
                    ),
                    "actual_page": (
                        document.metadata[
                            "page"
                        ]
                        if document
                        else ""
                    ),
                    "evidence_supports_claim": (
                        found
                    ),
                    "score": (
                        round(
                            float(score),
                            6,
                        )
                        if score is not None
                        else ""
                    ),
                }
            )

            if not found:
                failures.append(
                    {
                        "case_id": case["id"],
                        "claim": claim["claim"],
                    }
                )

    write_results(rows)

    assert not failures, (
        "Missing supporting citations: "
        f"{failures}"
    )


def test_each_case_requires_multiple_claims():
    fixture = load_fixture()

    for case in fixture["cases"]:
        assert len(
            case["claims"]
        ) >= 2


def test_missing_claim_is_detected_explicitly():
    fake_results = [
        (
            Document(
                page_content=(
                    "ChromaDB stores vector embeddings "
                    "for semantic retrieval."
                ),
                metadata={
                    "source": (
                        "architecture_reference.pdf"
                    ),
                    "page": 2,
                },
            ),
            0.9,
        )
    ]

    missing_claim = {
        "claim": (
            "Ollama runs the local language model."
        ),
        "expected_source": (
            "runtime_reference.pdf"
        ),
        "expected_page": 4,
        "required_terms": [
            "ollama",
            "local language model",
        ],
    }

    rank, document, score = (
        find_supporting_citation(
            fake_results,
            missing_claim,
        )
    )

    assert rank is None
    assert document is None
    assert score is None