import json
import re
from pathlib import Path
from statistics import mean
from uuid import uuid4

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama


ROOT = Path(__file__).parent.parent

DATASET_PATH = (
    ROOT
    / "evaluation"
    / "dataset.jsonl"
)

RESULTS_PATH = (
    ROOT
    / "evaluation"
    / "answer-results.jsonl"
)

METRICS_PATH = (
    ROOT
    / "evaluation"
    / "answer-metrics.json"
)

REPORT_PATH = (
    ROOT
    / "evaluation"
    / "final-evaluation-report.md"
)

TOP_K = 5
MODEL_NAME = "llama3.2:3b"
TEMPERATURE = 0

REFERENCE_TOKEN_RECALL_THRESHOLD = 0.50


STOP_WORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "to",
    "of",
    "in",
    "on",
    "for",
    "with",
    "from",
    "is",
    "are",
    "was",
    "were",
    "be",
    "by",
    "as",
    "it",
    "that",
    "this",
    "its",
    "into",
    "what",
    "which",
    "how",
    "does",
    "do",
    "used",
    "use",
    "uses",
}


ABSTENTION_TERMS = [
    "answer cannot be found",
    "cannot be found",
    "not enough information",
    "insufficient information",
    "not provided",
    "not stated",
    "does not contain",
    "cannot determine",
    "answer not found",
]


CONFLICT_TERMS = [
    "conflict",
    "conflicting",
    "disagree",
    "disagreement",
    "inconsistent",
    "different",
]


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


def load_json(path):
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def normalize(text):
    text = text.lower()

    text = re.sub(
        r"[^a-z0-9\s-]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def meaningful_tokens(text):
    return {
        token
        for token in normalize(text).split()
        if (
            len(token) > 2
            and token not in STOP_WORDS
        )
    }


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

    for file_name in [
        "source_a.txt",
        "source_b.txt",
    ]:
        path = (
            conflict_dir
            / file_name
        )

        text = path.read_text(
            encoding="utf-8"
        ).strip()

        documents.append(
            Document(
                page_content=text,
                metadata={
                    "source": file_name,
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
        documents=collect_controlled_documents(),
        embedding=get_embeddings(),
        collection_name=(
            f"answer_eval_{uuid4().hex}"
        ),
    )


def retrieve(
    vector_store,
    question,
):
    return (
        vector_store
        .similarity_search_with_relevance_scores(
            question,
            k=TOP_K,
        )
    )


def build_context(results):
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

    return "\n\n".join(parts)


def generate_answer(
    model,
    question,
    results,
):
    context = build_context(
        results
    )

    prompt = f"""
Answer the question using only the retrieved context below.

Important rules:

1. Inspect all retrieved results before deciding that
   the answer is unavailable.

2. If at least one retrieved result directly supports
   the question, answer using that evidence.

3. Ignore retrieved results that are unrelated to the
   specific question.

4. For questions requiring multiple facts, combine the
   relevant facts from multiple retrieved results.

5. If sources provide conflicting facts:
   - explicitly state that the sources conflict
   - report each conflicting claim
   - identify the source supporting each claim
   - do not choose one claim as definitively true unless
     the supplied evidence resolves the conflict

6. Only respond with:
   ANSWER CANNOT BE FOUND IN THE PROVIDED DOCUMENT.
   when none of the retrieved results contains evidence
   sufficient to answer the question.

7. Do not use outside knowledge.
8. Do not invent facts.
9. Keep the answer concise and factual.

Retrieved context:
{context}

Question:
{question}

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


def reference_token_recall(
    answer,
    reference_answer,
):
    reference_tokens = (
        meaningful_tokens(
            reference_answer
        )
    )

    answer_tokens = meaningful_tokens(
        answer
    )

    if not reference_tokens:
        return 1.0

    overlap = (
        reference_tokens
        & answer_tokens
    )

    return (
        len(overlap)
        / len(reference_tokens)
    )


def is_abstention(answer):
    normalized = normalize(answer)

    return any(
        term in normalized
        for term in ABSTENTION_TERMS
    )


def acknowledges_conflict(answer):
    normalized = normalize(answer)

    return any(
        term in normalized
        for term in CONFLICT_TERMS
    )


def result_matches_section(
    document,
    section,
):
    return (
        document.metadata.get("source")
        == section["source"]
        and document.metadata.get("page")
        == section["page"]
        and section["marker"]
        in document.page_content
    )


def evaluate_citations(
    results,
    expected_sections,
):
    found_sections = []

    citation_rows = []

    for section in expected_sections:
        match_rank = None
        match_score = None

        for rank, (
            document,
            score,
        ) in enumerate(
            results,
            start=1,
        ):
            if result_matches_section(
                document,
                section,
            ):
                match_rank = rank
                match_score = float(
                    score
                )
                break

        found = (
            match_rank is not None
        )

        if found:
            found_sections.append(
                section["marker"]
            )

        citation_rows.append(
            {
                "source": (
                    section["source"]
                ),
                "page": (
                    section["page"]
                ),
                "marker": (
                    section["marker"]
                ),
                "found": found,
                "rank": match_rank,
                "score": (
                    round(
                        match_score,
                        6,
                    )
                    if match_score
                    is not None
                    else None
                ),
            }
        )

    if expected_sections:
        coverage = (
            len(found_sections)
            / len(expected_sections)
        )
    else:
        coverage = None

    return (
        coverage,
        citation_rows,
    )


def evaluate_answer_case(
    case,
    answer,
    citation_coverage,
):
    if not case["answerable"]:
        abstained = is_abstention(
            answer
        )

        return {
            "answer_correct": (
                None
            ),
            "reference_token_recall": (
                None
            ),
            "abstained": abstained,
            "conflict_acknowledged": (
                None
            ),
            "overall_pass": abstained,
        }

    reference_answer = (
        case["reference_answer"]
    )

    token_recall = (
        reference_token_recall(
            answer,
            reference_answer,
        )
    )

    answer_correct = (
        token_recall
        >= REFERENCE_TOKEN_RECALL_THRESHOLD
    )

    conflict_acknowledged = None

    if (
        case["question_type"]
        == "conflicting"
    ):
        conflict_acknowledged = (
            acknowledges_conflict(
                answer
            )
        )

        answer_correct = (
            answer_correct
            and conflict_acknowledged
            and "30" in normalize(answer)
            and "60" in normalize(answer)
        )

    citation_complete = (
        citation_coverage == 1.0
    )

    overall = (
        answer_correct
        and citation_complete
    )

    return {
        "answer_correct": (
            answer_correct
        ),
        "reference_token_recall": (
            round(
                token_recall,
                4,
            )
        ),
        "abstained": None,
        "conflict_acknowledged": (
            conflict_acknowledged
        ),
        "overall_pass": (
            overall
        ),
    }


def run_evaluation():
    dataset = load_dataset()

    vector_store = (
        build_vector_store()
    )

    model = ChatOllama(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
    )

    records = []

    for case in dataset:
        results = retrieve(
            vector_store,
            case["question"],
        )

        answer, prompt = (
            generate_answer(
                model,
                case["question"],
                results,
            )
        )

        citation_coverage, citations = (
            evaluate_citations(
                results,
                case[
                    "expected_sections"
                ],
            )
        )

        answer_eval = (
            evaluate_answer_case(
                case,
                answer,
                citation_coverage,
            )
        )

        records.append(
            {
                "id": case["id"],
                "question_type": (
                    case["question_type"]
                ),
                "question": (
                    case["question"]
                ),
                "answerable": (
                    case["answerable"]
                ),
                "reference_answer": (
                    case[
                        "reference_answer"
                    ]
                ),
                "model_answer": answer,
                "answer_correct": (
                    answer_eval[
                        "answer_correct"
                    ]
                ),
                "reference_token_recall": (
                    answer_eval[
                        "reference_token_recall"
                    ]
                ),
                "abstained": (
                    answer_eval[
                        "abstained"
                    ]
                ),
                "conflict_acknowledged": (
                    answer_eval[
                        "conflict_acknowledged"
                    ]
                ),
                "citation_coverage": (
                    citation_coverage
                ),
                "citations": citations,
                "overall_pass": (
                    answer_eval[
                        "overall_pass"
                    ]
                ),
                "model_name": MODEL_NAME,
                "temperature": (
                    TEMPERATURE
                ),
                "top_k": TOP_K,
                "prompt": prompt,
            }
        )

    return records


def write_results(records):
    with RESULTS_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        for record in records:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )


def calculate_metrics(records):
    answerable = [
        record
        for record in records
        if record["answerable"]
    ]

    unsupported = [
        record
        for record in records
        if not record["answerable"]
    ]

    answer_accuracy = mean(
        1.0
        if record[
            "answer_correct"
        ]
        else 0.0
        for record in answerable
    )

    full_citation_accuracy = mean(
        1.0
        if record[
            "citation_coverage"
        ] == 1.0
        else 0.0
        for record in answerable
    )

    mean_citation_coverage = mean(
        record[
            "citation_coverage"
        ]
        for record in answerable
    )

    abstention_accuracy = mean(
        1.0
        if record["abstained"]
        else 0.0
        for record in unsupported
    )

    overall_accuracy = mean(
        1.0
        if record[
            "overall_pass"
        ]
        else 0.0
        for record in records
    )

    failures = [
        {
            "id": record["id"],
            "question_type": (
                record[
                    "question_type"
                ]
            ),
            "question": (
                record["question"]
            ),
            "model_answer": (
                record[
                    "model_answer"
                ]
            ),
            "answer_correct": (
                record[
                    "answer_correct"
                ]
            ),
            "abstained": (
                record["abstained"]
            ),
            "citation_coverage": (
                record[
                    "citation_coverage"
                ]
            ),
        }
        for record in records
        if not record["overall_pass"]
    ]

    return {
        "total_cases": len(
            records
        ),
        "answerable_cases": len(
            answerable
        ),
        "unsupported_cases": len(
            unsupported
        ),
        "answer_correctness_accuracy": (
            answer_accuracy
        ),
        "full_citation_accuracy": (
            full_citation_accuracy
        ),
        "mean_citation_coverage": (
            mean_citation_coverage
        ),
        "abstention_accuracy": (
            abstention_accuracy
        ),
        "overall_case_pass_rate": (
            overall_accuracy
        ),
        "failure_count": len(
            failures
        ),
        "failures": failures,
    }


def write_metrics(metrics):
    METRICS_PATH.write_text(
        json.dumps(
            metrics,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def write_report(
    metrics,
    records,
):
    failures = metrics[
        "failures"
    ]

    lines = [
        "# Final Answer Evaluation Report",
        "",
        "## Purpose",
        "",
        (
            "This evaluation measures answer correctness, "
            "citation coverage, and abstention behavior "
            "using the fixed reference dataset."
        ),
        "",
        "## Evaluation Method",
        "",
        "### Answer Correctness",
        "",
        (
            "Answerable cases are compared with the "
            "human-defined reference answer using normalized "
            "meaningful-token recall."
        ),
        "",
        (
            "A case passes the automated answer-correctness "
            "check when reference token recall is at least "
            f"`{REFERENCE_TOKEN_RECALL_THRESHOLD:.2f}`."
        ),
        "",
        (
            "Exact string equality is not required."
        ),
        "",
        (
            "Conflict cases additionally require the answer "
            "to acknowledge disagreement and preserve both "
            "30-second and 60-second claims."
        ),
        "",
        "### Citation Accuracy",
        "",
        (
            "Expected citations are evaluated against the "
            "human-defined source, page, and evidence marker."
        ),
        "",
        (
            "A citation case is fully correct only when all "
            "expected evidence sections appear within the "
            "top-five retrieved results."
        ),
        "",
        "### Abstention",
        "",
        (
            "Unanswerable and irrelevant questions are "
            "evaluated separately."
        ),
        "",
        (
            "They pass only when the generated answer "
            "explicitly states that the evidence is "
            "insufficient or the answer cannot be found."
        ),
        "",
        "## Model Configuration",
        "",
        f"- Model: `{MODEL_NAME}`",
        f"- Temperature: `{TEMPERATURE}`",
        f"- Retrieval top-k: `{TOP_K}`",
        "",
        "## Dataset",
        "",
        (
            f"- Total cases: "
            f"`{metrics['total_cases']}`"
        ),
        (
            f"- Answerable cases: "
            f"`{metrics['answerable_cases']}`"
        ),
        (
            f"- Unsupported cases: "
            f"`{metrics['unsupported_cases']}`"
        ),
        "",
        "## Numerical Results",
        "",
        (
            "- Answer correctness accuracy: "
            f"`{metrics['answer_correctness_accuracy']:.4f}`"
        ),
        (
            "- Full citation accuracy: "
            f"`{metrics['full_citation_accuracy']:.4f}`"
        ),
        (
            "- Mean citation coverage: "
            f"`{metrics['mean_citation_coverage']:.4f}`"
        ),
        (
            "- Abstention accuracy: "
            f"`{metrics['abstention_accuracy']:.4f}`"
        ),
        (
            "- Overall case pass rate: "
            f"`{metrics['overall_case_pass_rate']:.4f}`"
        ),
        (
            "- Failure count: "
            f"`{metrics['failure_count']}`"
        ),
        "",
        "## Failure Examples",
        "",
    ]

    if not failures:
        lines.append(
            "No automated evaluation failures were observed."
        )

    else:
        for failure in failures:
            lines.extend(
                [
                    (
                        f"### {failure['id']}"
                    ),
                    "",
                    (
                        f"- Type: "
                        f"`{failure['question_type']}`"
                    ),
                    (
                        f"- Question: "
                        f"{failure['question']}"
                    ),
                    (
                        "- Answer correct: "
                        f"`{failure['answer_correct']}`"
                    ),
                    (
                        "- Abstained: "
                        f"`{failure['abstained']}`"
                    ),
                    (
                        "- Citation coverage: "
                        f"`{failure['citation_coverage']}`"
                    ),
                    "",
                    "Model answer:",
                    "",
                    "```text",
                    failure[
                        "model_answer"
                    ],
                    "```",
                    "",
                ]
            )

    lines.extend(
        [
            "## Important Limitations",
            "",
            (
                "This evaluation does not use another language "
                "model as the sole judge of correctness."
            ),
            "",
            (
                "Automated answer scoring uses lexical concept "
                "coverage against human-defined reference "
                "answers. This makes the rule reproducible and "
                "inspectable, but it is not a complete semantic "
                "understanding metric."
            ),
            "",
            (
                "Equivalent wording may occasionally receive a "
                "lower score if it uses substantially different "
                "vocabulary from the reference answer."
            ),
            "",
            (
                "Conversely, lexical overlap alone cannot prove "
                "that every generated statement is logically "
                "correct."
            ),
            "",
            (
                "Citation evaluation verifies expected source, "
                "page, and controlled evidence markers, but does "
                "not replace human review of nuanced claims."
            ),
            "",
            (
                "Abstention detection is based on explicit "
                "failure phrases and may not capture every "
                "possible wording of uncertainty."
            ),
            "",
            (
                "For these reasons, automated metrics should be "
                "treated as reproducible engineering indicators, "
                "not as absolute truth."
            ),
            "",
            "## Reproducibility",
            "",
            (
                "Detailed per-case outputs are stored in "
                "`evaluation/answer-results.jsonl`."
            ),
            "",
            (
                "Each record includes the model answer, expected "
                "citations, retrieval coverage, prompt, model "
                "name, temperature, and pass/fail fields."
            ),
            "",
            "## Conclusion",
            "",
            (
                "The evaluation combines human-authored reference "
                "data with transparent automated rules for answer "
                "correctness, citation support, and abstention."
            ),
            "",
            (
                "Failures remain inspectable at the individual "
                "question level rather than being hidden behind "
                "aggregate metrics."
            ),
        ]
    )

    REPORT_PATH.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main():
    records = run_evaluation()

    write_results(
        records
    )

    metrics = calculate_metrics(
        records
    )

    write_metrics(
        metrics
    )

    write_report(
        metrics,
        records,
    )

    print(
        f"Total cases: "
        f"{metrics['total_cases']}"
    )

    print(
        "Answer correctness: "
        f"{metrics['answer_correctness_accuracy']:.4f}"
    )

    print(
        "Full citation accuracy: "
        f"{metrics['full_citation_accuracy']:.4f}"
    )

    print(
        "Abstention accuracy: "
        f"{metrics['abstention_accuracy']:.4f}"
    )

    print(
        "Overall pass rate: "
        f"{metrics['overall_case_pass_rate']:.4f}"
    )

    print(
        f"Failures: "
        f"{metrics['failure_count']}"
    )


if __name__ == "__main__":
    main()