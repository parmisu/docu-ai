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
    / "retrieval_cases.json"
)

RESULTS_PATH = (
    Path(__file__).parent.parent
    / "evaluation"
    / "retrieval-results.csv"
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
            f"retrieval_test_{uuid4().hex}"
        ),
    )


def find_expected_rank(
    results,
    expected_marker,
):
    for rank, (document, score) in enumerate(
        results,
        start=1,
    ):
        if expected_marker in document.page_content:
            return rank

    return None


def write_results_csv(rows):
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
                "expected_rank",
                "result_rank",
                "result_page",
                "result_source",
                "score",
                "result_text",
            ],
        )

        writer.writeheader()
        writer.writerows(rows)


def test_expected_reference_is_in_top_five():
    fixture = load_fixture()
    vector_store = build_vector_store()

    csv_rows = []

    for query_case in fixture["queries"]:
        results = (
            vector_store
            .similarity_search_with_relevance_scores(
                query_case["question"],
                k=TOP_K,
            )
        )

        assert len(results) > 0

        expected_rank = find_expected_rank(
            results,
            query_case["expected_marker"],
        )

        assert expected_rank is not None, (
            "Expected reference chunk was not "
            "found in the top five results for: "
            f"{query_case['question']}"
        )

        assert 1 <= expected_rank <= TOP_K

        expected_result = results[
            expected_rank - 1
        ][0]

        assert (
            expected_result.metadata["page"]
            == query_case["expected_page"]
        )

        for rank, (
            document,
            score,
        ) in enumerate(
            results,
            start=1,
        ):
            csv_rows.append(
                {
                    "question": (
                        query_case["question"]
                    ),
                    "expected_marker": (
                        query_case[
                            "expected_marker"
                        ]
                    ),
                    "expected_page": (
                        query_case[
                            "expected_page"
                        ]
                    ),
                    "expected_rank": (
                        expected_rank
                    ),
                    "result_rank": rank,
                    "result_page": (
                        document.metadata[
                            "page"
                        ]
                    ),
                    "result_source": (
                        document.metadata[
                            "source"
                        ]
                    ),
                    "score": round(
                        float(score),
                        6,
                    ),
                    "result_text": (
                        document.page_content
                    ),
                }
            )

    write_results_csv(csv_rows)


def test_top_five_results_are_inspectable():
    fixture = load_fixture()
    vector_store = build_vector_store()

    for query_case in fixture["queries"]:
        results = (
            vector_store
            .similarity_search_with_relevance_scores(
                query_case["question"],
                k=TOP_K,
            )
        )

        assert len(results) <= TOP_K
        assert len(results) > 0

        for document, score in results:
            assert document.page_content
            assert document.metadata["source"]
            assert document.metadata["page"] >= 1
            assert isinstance(
                float(score),
                float,
            )