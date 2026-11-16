import csv
import json
import re
from pathlib import Path

from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama


ROOT = Path(__file__).parent.parent

FIXTURE_PATH = (
    ROOT
    / "tests"
    / "fixtures"
    / "unanswerable_questions.json"
)

RESULTS_PATH = (
    ROOT
    / "evaluation"
    / "abstention-results.csv"
)


ABSTENTION_PHRASES = [
    "answer cannot be found",
    "cannot be found",
    "not enough information",
    "insufficient information",
    "not provided",
    "not stated",
    "does not contain",
    "cannot determine",
    "unknown",
]


def load_fixture():
    return json.loads(
        FIXTURE_PATH.read_text(
            encoding="utf-8"
        )
    )


def normalize(text):
    text = text.lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def generate_answer(
    question,
    context,
):
    model = ChatOllama(
        model="llama3.2:3b",
        temperature=0,
    )

    prompt = f"""
Answer using only the supplied context.

If the context does not contain enough evidence
to answer the question, explicitly say:

ANSWER CANNOT BE FOUND IN THE PROVIDED DOCUMENT.

Do not guess.
Do not use outside knowledge.
Do not invent facts.
Do not attribute unsupported information to the document.

Context:
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

    return response.content.strip()


def is_abstention(answer):
    normalized_answer = normalize(
        answer
    )

    return any(
        phrase in normalized_answer
        for phrase in ABSTENTION_PHRASES
    )


def contains_unsupported_claim(
    answer,
    unsupported_terms,
):
    normalized_answer = normalize(
        answer
    )

    return any(
        normalize(term) in normalized_answer
        for term in unsupported_terms
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
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "id",
                "question",
                "model_answer",
                "abstained",
                "unsupported_claim_detected",
                "overall_result",
            ],
        )

        writer.writeheader()
        writer.writerows(rows)


def test_unanswerable_questions_trigger_abstention():
    fixture = load_fixture()

    context = fixture[
        "document_context"
    ]

    result_rows = []
    failures = []

    for case in fixture["cases"]:
        answer = generate_answer(
            case["question"],
            context,
        )

        abstained = is_abstention(
            answer
        )

        unsupported_claim = (
            contains_unsupported_claim(
                answer,
                case[
                    "unsupported_terms"
                ],
            )
        )

        overall = (
            abstained
            and not unsupported_claim
        )

        result_rows.append(
            {
                "id": case["id"],
                "question": (
                    case["question"]
                ),
                "model_answer": answer,
                "abstained": abstained,
                "unsupported_claim_detected": (
                    unsupported_claim
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
                    "answer": answer,
                    "abstained": abstained,
                    "unsupported_claim_detected": (
                        unsupported_claim
                    ),
                }
            )

    write_results(
        result_rows
    )

    assert not failures, (
        "Abstention failures: "
        f"{failures}"
    )


def test_fixture_questions_are_not_supported_by_context():
    fixture = load_fixture()

    normalized_context = normalize(
        fixture["document_context"]
    )

    for case in fixture["cases"]:
        for term in case[
            "unsupported_terms"
        ]:
            assert (
                normalize(term)
                not in normalized_context
            )