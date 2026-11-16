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
    / "citation_cases.json"
)

RESULTS_PATH = (
    ROOT
    / "evaluation"
    / "citation-accuracy-results.csv"
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
            f"citation_test_{uuid4().hex}"
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


def find_expected_citation(
    results,
    expected_source,
    expected_page,
):
    for rank, (
        document,
        score,
    ) in enumerate(
        results,
        start=1,
    ):
        if (
            document.metadata["source"]
            == expected_source
            and document.metadata["page"]
            == expected_page
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
                "id",
                "question",
                "claim",
                "expected_source",
                "expected_page",
                "citation_rank",
                "actual_source",
                "actual_page",
                "source_correct",
                "page_correct",
                "evidence_supports_claim",
                "score",
                "overall_result",
            ],
        )

        writer.writeheader()
        writer.writerows(rows)


def test_citations_match_source_page_and_claim():
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

        rank, document, score = (
            find_expected_citation(
                results,
                case["expected_source"],
                case["expected_page"],
            )
        )

        citation_found = (
            document is not None
        )

        source_correct = (
            citation_found
            and document.metadata["source"]
            == case["expected_source"]
        )

        page_correct = (
            citation_found
            and document.metadata["page"]
            == case["expected_page"]
        )

        evidence_correct = (
            citation_found
            and evidence_supports_claim(
                document.page_content,
                case[
                    "required_evidence_terms"
                ],
            )
        )

        overall = (
            citation_found
            and source_correct
            and page_correct
            and evidence_correct
        )

        rows.append(
            {
                "id": case["id"],
                "question": (
                    case["question"]
                ),
                "claim": case["claim"],
                "expected_source": (
                    case["expected_source"]
                ),
                "expected_page": (
                    case["expected_page"]
                ),
                "citation_rank": (
                    rank
                    if rank is not None
                    else ""
                ),
                "actual_source": (
                    document.metadata["source"]
                    if document
                    else ""
                ),
                "actual_page": (
                    document.metadata["page"]
                    if document
                    else ""
                ),
                "source_correct": (
                    source_correct
                ),
                "page_correct": (
                    page_correct
                ),
                "evidence_supports_claim": (
                    evidence_correct
                ),
                "score": (
                    round(
                        float(score),
                        6,
                    )
                    if score is not None
                    else ""
                ),
                "overall_result": (
                    "PASS"
                    if overall
                    else "FAIL"
                ),
            }
        )

        if not overall:
            failures.append(
                {
                    "id": case["id"],
                    "citation_found": (
                        citation_found
                    ),
                    "source_correct": (
                        source_correct
                    ),
                    "page_correct": (
                        page_correct
                    ),
                    "evidence_supports_claim": (
                        evidence_correct
                    ),
                }
            )

    write_results(rows)

    assert not failures, (
        "Citation accuracy failures: "
        f"{failures}"
    )


def test_page_numbering_is_one_based():
    fixture = load_fixture()

    pages = [
        item["page"]
        for item in fixture["documents"]
    ]

    assert min(pages) >= 1


def test_citation_requires_evidence_not_metadata_only():
    fixture = load_fixture()

    distractor = next(
        item
        for item in fixture[
            "documents"
        ]
        if item["page"] == 6
    )

    for case in fixture["cases"]:
        assert not evidence_supports_claim(
            distractor["text"],
            case[
                "required_evidence_terms"
            ],
        )