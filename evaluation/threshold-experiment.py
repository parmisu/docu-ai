import csv
import json
from pathlib import Path
from uuid import uuid4

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings


ROOT = Path(__file__).parent.parent

RETRIEVAL_FIXTURE = (
    ROOT
    / "tests"
    / "fixtures"
    / "retrieval_cases.json"
)

IRRELEVANT_FIXTURE = (
    ROOT
    / "tests"
    / "fixtures"
    / "irrelevant_questions.json"
)

OUTPUT_PATH = (
    ROOT
    / "evaluation"
    / "threshold-results.csv"
)

TOP_K = 5

THRESHOLDS = [
    0.00,
    0.05,
    0.10,
    0.15,
    0.20,
    0.25,
    0.30,
    0.40,
    0.50,
]


def load_json(path):
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=(
            "sentence-transformers/"
            "all-MiniLM-L6-v2"
        )
    )


def build_documents():
    relevant_fixture = load_json(
        RETRIEVAL_FIXTURE
    )

    irrelevant_fixture = load_json(
        IRRELEVANT_FIXTURE
    )

    seen = set()
    documents = []

    for item in (
        relevant_fixture["documents"]
        + irrelevant_fixture["documents"]
    ):
        key = (
            item["text"],
            item["source"],
            item["page"],
        )

        if key in seen:
            continue

        seen.add(key)

        documents.append(
            Document(
                page_content=item["text"],
                metadata={
                    "source": item["source"],
                    "page": item["page"],
                },
            )
        )

    return documents


def build_cases():
    relevant_fixture = load_json(
        RETRIEVAL_FIXTURE
    )

    irrelevant_fixture = load_json(
        IRRELEVANT_FIXTURE
    )

    cases = []

    for case in relevant_fixture["queries"]:
        cases.append(
            {
                "question": (
                    case["question"]
                ),
                "expected_type": "RELEVANT",
                "expected_marker": (
                    case["expected_marker"]
                ),
            }
        )

    for case in irrelevant_fixture[
        "questions"
    ]:
        cases.append(
            {
                "question": (
                    case["question"]
                ),
                "expected_type": "IRRELEVANT",
                "expected_marker": "",
            }
        )

    return cases


def build_vector_store():
    return Chroma.from_documents(
        documents=build_documents(),
        embedding=get_embeddings(),
        collection_name=(
            f"threshold_test_{uuid4().hex}"
        ),
    )


def evaluate_threshold(
    vector_store,
    case,
    threshold,
):
    results = (
        vector_store
        .similarity_search_with_relevance_scores(
            case["question"],
            k=TOP_K,
        )
    )

    accepted = [
        (document, score)
        for document, score in results
        if float(score) >= threshold
    ]

    best_score = (
        max(float(score) for _, score in results)
        if results
        else None
    )

    expected_found = False
    expected_rank = None
    expected_score = None

    if case["expected_type"] == "RELEVANT":
        for rank, (
            document,
            score,
        ) in enumerate(
            results,
            start=1,
        ):
            if (
                case["expected_marker"]
                in document.page_content
            ):
                expected_rank = rank
                expected_score = float(score)

                if (
                    float(score)
                    >= threshold
                ):
                    expected_found = True

                break

        outcome = (
            "TRUE_POSITIVE"
            if expected_found
            else "FALSE_NEGATIVE"
        )

    else:
        if accepted:
            outcome = "FALSE_POSITIVE"
        else:
            outcome = "TRUE_NEGATIVE"

    return {
        "threshold": threshold,
        "question": case["question"],
        "expected_type": (
            case["expected_type"]
        ),
        "expected_marker": (
            case["expected_marker"]
        ),
        "best_score": (
            round(best_score, 6)
            if best_score is not None
            else ""
        ),
        "expected_rank": (
            expected_rank
            if expected_rank is not None
            else ""
        ),
        "expected_score": (
            round(expected_score, 6)
            if expected_score is not None
            else ""
        ),
        "accepted_result_count": (
            len(accepted)
        ),
        "outcome": outcome,
    }


def main():
    vector_store = build_vector_store()
    cases = build_cases()

    rows = []

    for threshold in THRESHOLDS:
        for case in cases:
            rows.append(
                evaluate_threshold(
                    vector_store,
                    case,
                    threshold,
                )
            )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "threshold",
                "question",
                "expected_type",
                "expected_marker",
                "best_score",
                "expected_rank",
                "expected_score",
                "accepted_result_count",
                "outcome",
            ],
        )

        writer.writeheader()
        writer.writerows(rows)

    print(
        f"Wrote results to {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()