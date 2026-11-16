import csv
import json
import re
from pathlib import Path

from langchain_core.messages import HumanMessage
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
    / "answer-correctness-results.csv"
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


def concept_present(
    answer,
    concept,
):
    """
    Check whether the important words in a concept
    appear in the generated answer.

    Exact sentence matching is not required.
    """
    normalized_answer = normalize(answer)

    concept_words = [
        word
        for word in normalize(
            concept
        ).split()
        if len(word) > 2
    ]

    return all(
        word in normalized_answer
        for word in concept_words
    )


def concept_group_present(
    answer,
    alternatives,
):
    """
    A concept group passes when at least one
    equivalent alternative is present.
    """
    return any(
        concept_present(
            answer,
            alternative,
        )
        for alternative in alternatives
    )


def answer_is_grounded(
    answer,
    context,
):
    """
    Check that meaningful answer terms are
    supported by the supplied context.
    """
    stop_words = {
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "from",
        "are",
        "was",
        "used",
        "uses",
        "use",
        "to",
        "a",
        "an",
        "of",
        "in",
        "by",
        "is",
        "it",
    }

    answer_words = {
        word
        for word in normalize(
            answer
        ).split()
        if (
            len(word) > 2
            and word not in stop_words
        )
    }

    context_words = set(
        normalize(context).split()
    )

    unsupported = (
        answer_words
        - context_words
    )

    return len(unsupported) == 0


def generate_answer(
    question,
    context,
):
    model = ChatOllama(
        model="llama3.2:3b",
        temperature=0,
    )

    prompt = f"""
Answer the question using only the supplied context.

Identify the exact person, tool, framework, database,
or fact that directly answers the question.

Do not answer with a related application or concept
unless it directly answers the question.

If the answer is not supported by the context,
say that the answer cannot be found.

Keep the answer short and factual.

Context:
{context}

Question:
{question}

Direct answer:
"""

    response = model.invoke(
        [
            HumanMessage(
                content=prompt
            )
        ]
    )

    return response.content.strip()


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
                "reference_answer",
                "model_answer",
                "required_facts_pass",
                "forbidden_facts_pass",
                "grounded",
                "overall_result",
            ],
        )

        writer.writeheader()
        writer.writerows(rows)


def test_generated_answers_match_reference_facts():
    dataset = load_dataset()

    result_rows = []
    failures = []

    for case in dataset:
        answer = generate_answer(
            case["question"],
            case["context"],
        )

        required_pass = all(
            concept_group_present(
                answer,
                group,
            )
            for group in case[
                "required_concept_groups"
            ]
        )

        forbidden_pass = all(
            not concept_present(
                answer,
                fact,
            )
            for fact in case[
                "forbidden_facts"
            ]
        )

        grounded = answer_is_grounded(
            answer,
            case["context"],
        )

        overall = (
            required_pass
            and forbidden_pass
            and grounded
        )

        result_rows.append(
            {
                "id": case["id"],
                "question": case["question"],
                "reference_answer": (
                    case["reference_answer"]
                ),
                "model_answer": answer,
                "required_facts_pass": (
                    required_pass
                ),
                "forbidden_facts_pass": (
                    forbidden_pass
                ),
                "grounded": grounded,
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
                    "required_facts_pass": (
                        required_pass
                    ),
                    "forbidden_facts_pass": (
                        forbidden_pass
                    ),
                    "grounded": grounded,
                }
            )

    write_results(result_rows)

    assert not failures, (
        "Answer correctness failures: "
        f"{failures}"
    )


def test_dataset_defines_semantic_acceptance_rules():
    dataset = load_dataset()

    assert len(dataset) > 0

    for case in dataset:
        assert case["reference_answer"]

        assert case[
            "required_concept_groups"
        ]

        assert isinstance(
            case[
                "required_concept_groups"
            ],
            list,
        )

        for group in case[
            "required_concept_groups"
        ]:
            assert isinstance(
                group,
                list,
            )

            assert len(group) > 0

        assert isinstance(
            case["forbidden_facts"],
            list,
        )