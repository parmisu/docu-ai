import csv
import json
from pathlib import Path
from statistics import mean
from uuid import uuid4

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings


ROOT = Path(__file__).parent.parent

DATASET_PATH = (
    ROOT
    / "evaluation"
    / "dataset.jsonl"
)

RESULTS_PATH = (
    ROOT
    / "evaluation"
    / "retrieval-results.csv"
)

METRICS_PATH = (
    ROOT
    / "evaluation"
    / "retrieval-metrics.json"
)

REPORT_PATH = (
    ROOT
    / "evaluation"
    / "retrieval-report.md"
)

TOP_K = 5


def load_json(path):
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def load_dataset():
    rows = []

    with DATASET_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            line = line.strip()

            if line:
                rows.append(
                    json.loads(line)
                )

    return rows


def collect_controlled_documents():
    documents = []
    seen = set()

    fixture_paths = [
        (
            ROOT
            / "tests"
            / "fixtures"
            / "retrieval_cases.json"
        ),
        (
            ROOT
            / "tests"
            / "fixtures"
            / "multi_chunk_cases.json"
        ),
        (
            ROOT
            / "tests"
            / "fixtures"
            / "multi_source_cases.json"
        ),
    ]

    for path in fixture_paths:
        fixture = load_json(path)

        for item in fixture["documents"]:
            key = (
                item["source"],
                item["page"],
                item["text"],
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

    conflict_dir = (
        ROOT
        / "tests"
        / "fixtures"
        / "conflicting_documents"
    )

    conflict_files = [
        (
            conflict_dir
            / "source_a.txt"
        ),
        (
            conflict_dir
            / "source_b.txt"
        ),
    ]

    for path in conflict_files:
        text = path.read_text(
            encoding="utf-8"
        ).strip()

        key = (
            path.name,
            1,
            text,
        )

        if key in seen:
            continue

        seen.add(key)

        documents.append(
            Document(
                page_content=text,
                metadata={
                    "source": path.name,
                    "page": 1,
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


def build_vector_store():
    return Chroma.from_documents(
        documents=(
            collect_controlled_documents()
        ),
        embedding=get_embeddings(),
        collection_name=(
            f"retrieval_eval_{uuid4().hex}"
        ),
    )


def result_matches_section(
    document,
    section,
):
    source_matches = (
        document.metadata.get("source")
        == section["source"]
    )

    page_matches = (
        document.metadata.get("page")
        == section["page"]
    )

    marker_matches = (
        section["marker"]
        in document.page_content
    )

    return (
        source_matches
        and page_matches
        and marker_matches
    )


def evaluate_case(
    vector_store,
    case,
):
    results = (
        vector_store
        .similarity_search_with_relevance_scores(
            case["question"],
            k=TOP_K,
        )
    )

    expected_sections = (
        case["expected_sections"]
    )

    matched_sections = []
    relevant_ranks = []

    result_rows = []

    for rank, (
        document,
        score,
    ) in enumerate(
        results,
        start=1,
    ):
        matching_markers = []

        for section in expected_sections:
            if result_matches_section(
                document,
                section,
            ):
                matching_markers.append(
                    section["marker"]
                )

                if (
                    section["marker"]
                    not in matched_sections
                ):
                    matched_sections.append(
                        section["marker"]
                    )

                    relevant_ranks.append(
                        rank
                    )

        result_rows.append(
            {
                "case_id": case["id"],
                "question_type": (
                    case["question_type"]
                ),
                "question": (
                    case["question"]
                ),
                "result_rank": rank,
                "result_source": (
                    document.metadata.get(
                        "source",
                        "",
                    )
                ),
                "result_page": (
                    document.metadata.get(
                        "page",
                        "",
                    )
                ),
                "score": round(
                    float(score),
                    6,
                ),
                "relevant": bool(
                    matching_markers
                ),
                "matched_markers": (
                    "|".join(
                        matching_markers
                    )
                ),
                "result_text": (
                    document.page_content
                ),
            }
        )

    relevant_count = len(
        expected_sections
    )

    retrieved_relevant_count = len(
        matched_sections
    )

    recall_at_5 = (
        retrieved_relevant_count
        / relevant_count
    )

    if relevant_ranks:
        reciprocal_rank = (
            1
            / min(relevant_ranks)
        )
    else:
        reciprocal_rank = 0.0

    missed_markers = [
        section["marker"]
        for section in expected_sections
        if section["marker"]
        not in matched_sections
    ]

    return {
        "case_id": case["id"],
        "question": (
            case["question"]
        ),
        "question_type": (
            case["question_type"]
        ),
        "expected_section_count": (
            relevant_count
        ),
        "retrieved_relevant_count": (
            retrieved_relevant_count
        ),
        "recall_at_5": (
            recall_at_5
        ),
        "mrr_at_5": (
            reciprocal_rank
        ),
        "missed_markers": (
            missed_markers
        ),
        "rows": result_rows,
    }


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
                "question_type",
                "question",
                "result_rank",
                "result_source",
                "result_page",
                "score",
                "relevant",
                "matched_markers",
                "result_text",
            ],
        )

        writer.writeheader()
        writer.writerows(rows)


def write_metrics(
    evaluated_cases,
    excluded_cases,
):
    recalls = [
        case["recall_at_5"]
        for case in evaluated_cases
    ]

    reciprocal_ranks = [
        case["mrr_at_5"]
        for case in evaluated_cases
    ]

    perfect_recall_cases = sum(
        case["recall_at_5"] == 1.0
        for case in evaluated_cases
    )

    failures = [
        {
            "case_id": (
                case["case_id"]
            ),
            "question": (
                case["question"]
            ),
            "recall_at_5": (
                case["recall_at_5"]
            ),
            "mrr_at_5": (
                case["mrr_at_5"]
            ),
            "missed_markers": (
                case[
                    "missed_markers"
                ]
            ),
        }
        for case in evaluated_cases
        if case["recall_at_5"] < 1.0
    ]

    metrics = {
        "top_k": TOP_K,
        "evaluated_question_count": (
            len(evaluated_cases)
        ),
        "excluded_question_count": (
            len(excluded_cases)
        ),
        "excluded_question_types": (
            sorted(
                {
                    case[
                        "question_type"
                    ]
                    for case in excluded_cases
                }
            )
        ),
        "macro_recall_at_5": (
            mean(recalls)
            if recalls
            else 0.0
        ),
        "mrr_at_5": (
            mean(reciprocal_ranks)
            if reciprocal_ranks
            else 0.0
        ),
        "perfect_recall_case_count": (
            perfect_recall_cases
        ),
        "failure_count": (
            len(failures)
        ),
        "failures": failures,
    }

    METRICS_PATH.write_text(
        json.dumps(
            metrics,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return metrics


def write_report(
    metrics,
    evaluated_cases,
):
    lines = [
        "# Retrieval Evaluation Report",
        "",
        "## Purpose",
        "",
        (
            "This evaluation measures whether "
            "the expected evidence sections are "
            "retrieved within the top five results."
        ),
        "",
        "## Metrics",
        "",
        "### Recall@5",
        "",
        "For each question:",
        "",
        "```text",
        (
            "Recall@5 = relevant reference sections "
            "retrieved in top 5 / total reference sections"
        ),
        "```",
        "",
        (
            "The reported dataset-level Recall@5 "
            "is the macro average across eligible questions."
        ),
        "",
        "### MRR@5",
        "",
        "For each question:",
        "",
        "```text",
        (
            "RR@5 = 1 / rank of the first relevant result"
        ),
        "```",
        "",
        (
            "If no relevant result appears in the top five, "
            "the reciprocal rank is 0."
        ),
        "",
        (
            "MRR@5 is the mean reciprocal rank across "
            "eligible evaluation questions."
        ),
        "",
        "## Eligibility",
        "",
        (
            "Only questions with explicit expected reference "
            "sections are included in retrieval metrics."
        ),
        "",
        (
            "Unanswerable and irrelevant questions are "
            "excluded because they intentionally have no "
            "reference source."
        ),
        "",
        "Including them as retrieval failures would "
        "misrepresent retrieval quality.",
        "",
        "## Sample Counts",
        "",
        (
            "- Evaluated questions: "
            f"`{metrics['evaluated_question_count']}`"
        ),
        (
            "- Excluded questions: "
            f"`{metrics['excluded_question_count']}`"
        ),
        (
            "- Top K: "
            f"`{metrics['top_k']}`"
        ),
        "",
        "## Aggregate Results",
        "",
        (
            "- Macro Recall@5: "
            f"`{metrics['macro_recall_at_5']:.4f}`"
        ),
        (
            "- MRR@5: "
            f"`{metrics['mrr_at_5']:.4f}`"
        ),
        (
            "- Perfect-recall questions: "
            f"`{metrics['perfect_recall_case_count']}`"
        ),
        (
            "- Questions with retrieval misses: "
            f"`{metrics['failure_count']}`"
        ),
        "",
        "## Failure Analysis",
        "",
    ]

    failures = metrics["failures"]

    if not failures:
        lines.append(
            "No eligible question missed a reference section "
            "within the top five results."
        )

    else:
        for failure in failures:
            lines.extend(
                [
                    (
                        f"### {failure['case_id']}"
                    ),
                    "",
                    failure["question"],
                    "",
                    (
                        "- Recall@5: "
                        f"`{failure['recall_at_5']:.4f}`"
                    ),
                    (
                        "- RR@5: "
                        f"`{failure['mrr_at_5']:.4f}`"
                    ),
                    (
                        "- Missed markers: "
                        f"`{', '.join(failure['missed_markers'])}`"
                    ),
                    "",
                ]
            )

    lines.extend(
        [
            "## Per-Question Summary",
            "",
            "| ID | Type | Expected | Found | Recall@5 | RR@5 |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )

    for case in evaluated_cases:
        lines.append(
            (
                f"| {case['case_id']} "
                f"| {case['question_type']} "
                f"| {case['expected_section_count']} "
                f"| {case['retrieved_relevant_count']} "
                f"| {case['recall_at_5']:.4f} "
                f"| {case['mrr_at_5']:.4f} |"
            )
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "Recall@5 measures evidence coverage, "
                "including multi-section questions."
            ),
            "",
            (
                "MRR@5 measures how early the first relevant "
                "section appears in the ranked results."
            ),
            "",
            (
                "The detailed CSV should be used to inspect "
                "ranking errors and individual retrieved chunks."
            ),
            "",
            "## Reproducibility",
            "",
            (
                "The evaluation uses the fixed reference dataset "
                "in `evaluation/dataset.jsonl`, the controlled "
                "fixture corpus, `k=5`, and the configured "
                "`all-MiniLM-L6-v2` embedding model."
            ),
        ]
    )

    REPORT_PATH.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main():
    dataset = load_dataset()

    eligible_cases = [
        case
        for case in dataset
        if case["expected_sections"]
    ]

    excluded_cases = [
        case
        for case in dataset
        if not case["expected_sections"]
    ]

    vector_store = build_vector_store()

    evaluated_cases = []
    all_result_rows = []

    for case in eligible_cases:
        evaluation = evaluate_case(
            vector_store,
            case,
        )

        evaluated_cases.append(
            evaluation
        )

        all_result_rows.extend(
            evaluation["rows"]
        )

    write_results(
        all_result_rows
    )

    metrics = write_metrics(
        evaluated_cases,
        excluded_cases,
    )

    write_report(
        metrics,
        evaluated_cases,
    )

    print(
        f"Evaluated questions: "
        f"{metrics['evaluated_question_count']}"
    )

    print(
        f"Excluded questions: "
        f"{metrics['excluded_question_count']}"
    )

    print(
        f"Recall@5: "
        f"{metrics['macro_recall_at_5']:.4f}"
    )

    print(
        f"MRR@5: "
        f"{metrics['mrr_at_5']:.4f}"
    )

    print(
        f"Failures: "
        f"{metrics['failure_count']}"
    )


if __name__ == "__main__":
    main()