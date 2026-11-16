import json
from pathlib import Path
from uuid import uuid4

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "irrelevant_questions.json"
)

REPORT_PATH = (
    Path(__file__).parent.parent
    / "evaluation"
    / "irrelevant-retrieval-report.md"
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
            f"irrelevant_test_{uuid4().hex}"
        ),
    )


def contains_required_evidence(
    document_text,
    required_terms,
):
    normalized = document_text.lower()

    return any(
        term.lower() in normalized
        for term in required_terms
    )


def write_report(report_cases, threshold):
    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    lines = [
        "# Irrelevant Retrieval Evaluation",
        "",
        "## Purpose",
        "",
        (
            "This evaluation checks how Docu AI behaves "
            "when a question has no supported answer in "
            "the indexed document."
        ),
        "",
        "A retrieved result is not treated as evidence",
        "solely because similarity search returned it.",
        "",
        "## Relevance Threshold",
        "",
        f"`{threshold}`",
        "",
        "## Results",
        "",
    ]

    for case in report_cases:
        lines.extend(
            [
                f"### Question: {case['question']}",
                "",
                f"- Best score: `{case['best_score']}`",
                (
                    "- Evidence found: "
                    f"`{case['evidence_found']}`"
                ),
                (
                    "- Decision: "
                    f"`{case['decision']}`"
                ),
                "",
                "| Rank | Page | Score | Evidence | Text |",
                "|---:|---:|---:|---|---|",
            ]
        )

        for result in case["results"]:
            safe_text = result["text"].replace(
                "|",
                "\\|",
            )

            lines.append(
                (
                    f"| {result['rank']} "
                    f"| {result['page']} "
                    f"| {result['score']} "
                    f"| {result['evidence']} "
                    f"| {safe_text} |"
                )
            )

        lines.append("")

    lines.extend(
        [
            "## Interpretation",
            "",
            (
                "Similarity alone is not sufficient to "
                "establish that the document contains a "
                "valid answer."
            ),
            "",
            (
                "A result may be semantically close to "
                "the question while still lacking the "
                "specific evidence needed to answer it."
            ),
        ]
    )

    REPORT_PATH.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def test_fixture_contains_no_required_answer_evidence():
    fixture = load_fixture()

    corpus = " ".join(
        item["text"].lower()
        for item in fixture["documents"]
    )

    for case in fixture["questions"]:
        for term in case[
            "required_answer_terms"
        ]:
            assert term.lower() not in corpus


def test_irrelevant_retrieval_is_not_valid_evidence():
    fixture = load_fixture()
    threshold = fixture[
        "relevance_threshold"
    ]

    vector_store = build_vector_store()

    report_cases = []

    for case in fixture["questions"]:
        results = (
            vector_store
            .similarity_search_with_relevance_scores(
                case["question"],
                k=TOP_K,
            )
        )

        assert len(results) > 0

        evidence_found = False
        result_rows = []

        for rank, (
            document,
            score,
        ) in enumerate(
            results,
            start=1,
        ):
            has_evidence = (
                contains_required_evidence(
                    document.page_content,
                    case[
                        "required_answer_terms"
                    ],
                )
            )

            evidence_found = (
                evidence_found
                or has_evidence
            )

            result_rows.append(
                {
                    "rank": rank,
                    "page": (
                        document.metadata["page"]
                    ),
                    "score": round(
                        float(score),
                        6,
                    ),
                    "evidence": has_evidence,
                    "text": (
                        document.page_content
                    ),
                }
            )

        best_score = max(
            float(score)
            for _, score in results
        )

        decision = (
            "SUPPORTED"
            if evidence_found
            else "UNSUPPORTED"
        )

        assert evidence_found is False
        assert decision == "UNSUPPORTED"

        if case[
            "expect_high_similarity_without_evidence"
        ]:
            assert best_score >= threshold

        report_cases.append(
            {
                "question": (
                    case["question"]
                ),
                "best_score": round(
                    best_score,
                    6,
                ),
                "evidence_found": (
                    evidence_found
                ),
                "decision": decision,
                "results": result_rows,
            }
        )

    write_report(
        report_cases,
        threshold,
    )


def test_retrieved_results_remain_inspectable():
    fixture = load_fixture()
    vector_store = build_vector_store()

    for case in fixture["questions"]:
        results = (
            vector_store
            .similarity_search_with_relevance_scores(
                case["question"],
                k=TOP_K,
            )
        )

        assert 0 < len(results) <= TOP_K

        for document, score in results:
            assert document.page_content
            assert document.metadata["source"]
            assert document.metadata["page"] >= 1

            float(score)