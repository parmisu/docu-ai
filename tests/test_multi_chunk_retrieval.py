import csv
import json
from pathlib import Path
from uuid import uuid4

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "multi_chunk_cases.json"
)

RESULTS_PATH = (
    Path(__file__).parent.parent
    / "evaluation"
    / "multi-chunk-results.csv"
)

TOP_K = 5


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


def build_vector_store():
    return Chroma.from_documents(
        documents=build_documents(),
        embedding=get_embeddings(),
        collection_name=(
            f"multi_chunk_test_{uuid4().hex}"
        ),
    )


def find_marker_rank(results, marker):
    for rank, (document, score) in enumerate(
        results,
        start=1,
    ):
        if marker in document.page_content:
            return rank, document, score

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
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "question",
                "expected_marker",
                "expected_page",
                "status",
                "rank",
                "retrieved_page",
                "retrieved_source",
                "score",
            ],
        )

        writer.writeheader()
        writer.writerows(rows)


def test_multi_chunk_information_is_retrieved():
    fixture = load_fixture()
    vector_store = build_vector_store()

    csv_rows = []
    failures = []

    for case in fixture["queries"]:
        results = (
            vector_store
            .similarity_search_with_relevance_scores(
                case["question"],
                k=TOP_K,
            )
        )

        assert len(results) > 0

        for expected in case[
            "expected_sections"
        ]:
            rank, document, score = (
                find_marker_rank(
                    results,
                    expected["marker"],
                )
            )

            if rank is None:
                csv_rows.append(
                    {
                        "question": (
                            case["question"]
                        ),
                        "expected_marker": (
                            expected["marker"]
                        ),
                        "expected_page": (
                            expected["page"]
                        ),
                        "status": "MISSING",
                        "rank": "",
                        "retrieved_page": "",
                        "retrieved_source": "",
                        "score": "",
                    }
                )

                failures.append(
                    (
                        case["question"],
                        expected["marker"],
                    )
                )

            else:
                csv_rows.append(
                    {
                        "question": (
                            case["question"]
                        ),
                        "expected_marker": (
                            expected["marker"]
                        ),
                        "expected_page": (
                            expected["page"]
                        ),
                        "status": "FOUND",
                        "rank": rank,
                        "retrieved_page": (
                            document.metadata[
                                "page"
                            ]
                        ),
                        "retrieved_source": (
                            document.metadata[
                                "source"
                            ]
                        ),
                        "score": round(
                            float(score),
                            6,
                        ),
                    }
                )

                assert (
                    document.metadata["page"]
                    == expected["page"]
                )

                assert 1 <= rank <= TOP_K

    write_results(csv_rows)

    assert not failures, (
        "Required multi-chunk information "
        f"was missing from top-{TOP_K}: "
        f"{failures}"
    )


def test_each_question_requires_multiple_sections():
    fixture = load_fixture()

    for case in fixture["queries"]:
        assert len(
            case["expected_sections"]
        ) >= 2

        markers = {
            section["marker"]
            for section
            in case["expected_sections"]
        }

        assert len(markers) >= 2