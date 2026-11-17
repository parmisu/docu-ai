import json
import platform
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
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
    / "reproducibility-results.jsonl"
)

REPORT_PATH = (
    ROOT
    / "evaluation"
    / "reproducibility-report.md"
)

MODEL_NAME = "llama3.2:3b"
TEMPERATURE = 0
RUNS_PER_QUESTION = 3


PROMPT_TEMPLATE = """
Use only the context below.

Return the shortest exact answer that directly answers
the question.

Prefer words or phrases that appear explicitly in the
context.

Do not answer with the name of the application unless
the question specifically asks for the application.

If the context does not contain the answer, respond:
ANSWER NOT FOUND

Context:
{context}

Question:
{question}

Answer:
""".strip()


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


def command_output(command):
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )

        output = (
            completed.stdout.strip()
            or completed.stderr.strip()
        )

        return output

    except Exception as exc:
        return f"Unavailable: {exc}"


def get_environment_info():
    ollama_version = command_output(
        ["ollama", "--version"]
    )

    ollama_list = command_output(
        ["ollama", "list"]
    )

    return {
        "timestamp_utc": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "python_version": (
            sys.version.replace(
                "\n",
                " ",
            )
        ),
        "platform": (
            platform.platform()
        ),
        "machine": (
            platform.machine()
        ),
        "ollama_version": (
            ollama_version
        ),
        "ollama_models": (
            ollama_list
        ),
        "model_name": MODEL_NAME,
        "temperature": TEMPERATURE,
        "runs_per_question": (
            RUNS_PER_QUESTION
        ),
        "prompt_template": (
            PROMPT_TEMPLATE
        ),
    }


def generate_answer(
    model,
    question,
    context,
):
    prompt = PROMPT_TEMPLATE.format(
        context=context,
        question=question,
    )

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


def run_experiment():
    dataset = load_dataset()
    environment = get_environment_info()

    model = ChatOllama(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
    )

    records = []

    for case in dataset:
        for run_number in range(
            1,
            RUNS_PER_QUESTION + 1,
        ):
            answer, prompt = (
                generate_answer(
                    model=model,
                    question=(
                        case["question"]
                    ),
                    context=(
                        case["context"]
                    ),
                )
            )

            records.append(
                {
                    "case_id": (
                        case["id"]
                    ),
                    "run_number": (
                        run_number
                    ),
                    "question": (
                        case["question"]
                    ),
                    "context": (
                        case["context"]
                    ),
                    "reference_answer": (
                        case[
                            "reference_answer"
                        ]
                    ),
                    "model_answer": answer,
                    "normalized_answer": (
                        normalize(answer)
                    ),
                    "model_name": (
                        MODEL_NAME
                    ),
                    "temperature": (
                        TEMPERATURE
                    ),
                    "prompt": prompt,
                    "environment": (
                        environment
                    ),
                }
            )

    return records, environment


def write_jsonl(records):
    RESULTS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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


def analyze(records):
    grouped = defaultdict(list)

    for record in records:
        grouped[
            record["case_id"]
        ].append(record)

    analysis = []

    for case_id, case_records in grouped.items():
        exact_answers = {
            record["model_answer"]
            for record in case_records
        }

        normalized_answers = {
            record[
                "normalized_answer"
            ]
            for record in case_records
        }

        analysis.append(
            {
                "case_id": case_id,
                "question": (
                    case_records[0][
                        "question"
                    ]
                ),
                "run_count": (
                    len(case_records)
                ),
                "unique_exact_answers": (
                    len(exact_answers)
                ),
                "unique_normalized_answers": (
                    len(normalized_answers)
                ),
                "exact_match_across_runs": (
                    len(exact_answers) == 1
                ),
                "normalized_match_across_runs": (
                    len(
                        normalized_answers
                    ) == 1
                ),
                "answers": [
                    record[
                        "model_answer"
                    ]
                    for record
                    in case_records
                ],
            }
        )

    return analysis


def write_report(
    environment,
    analysis,
):
    exact_stable = sum(
        item[
            "exact_match_across_runs"
        ]
        for item in analysis
    )

    normalized_stable = sum(
        item[
            "normalized_match_across_runs"
        ]
        for item in analysis
    )

    total_cases = len(analysis)

    lines = [
        "# Reproducibility Evaluation Report",
        "",
        "## Purpose",
        "",
        (
            "This experiment measures answer variation "
            "across repeated controlled runs of the same "
            "questions."
        ),
        "",
        (
            "The goal is not to require guaranteed "
            "bit-for-bit identical language-model output."
        ),
        "",
        (
            "Instead, the experiment records the model, "
            "settings, prompt, runtime conditions, and "
            "observed answer differences."
        ),
        "",
        "## Execution Configuration",
        "",
        f"- Model: `{environment['model_name']}`",
        (
            "- Temperature: "
            f"`{environment['temperature']}`"
        ),
        (
            "- Runs per question: "
            f"`{environment['runs_per_question']}`"
        ),
        (
            "- Python: "
            f"`{environment['python_version']}`"
        ),
        (
            "- Platform: "
            f"`{environment['platform']}`"
        ),
        (
            "- Machine architecture: "
            f"`{environment['machine']}`"
        ),
        "",
        "### Ollama Version",
        "",
        "```text",
        environment[
            "ollama_version"
        ],
        "```",
        "",
        "### Installed Ollama Models",
        "",
        "```text",
        environment[
            "ollama_models"
        ],
        "```",
        "",
        "## Prompt",
        "",
        "```text",
        environment[
            "prompt_template"
        ],
        "```",
        "",
        "## Results Summary",
        "",
        (
            f"- Total question cases: "
            f"`{total_cases}`"
        ),
        (
            "- Cases with identical exact output "
            f"across runs: `{exact_stable}`"
        ),
        (
            "- Cases with identical normalized output "
            f"across runs: `{normalized_stable}`"
        ),
        "",
        "## Per-Question Results",
        "",
    ]

    for item in analysis:
        lines.extend(
            [
                (
                    f"### {item['case_id']}"
                ),
                "",
                (
                    f"Question: "
                    f"{item['question']}"
                ),
                "",
                (
                    "- Exact output stable: "
                    f"`{item['exact_match_across_runs']}`"
                ),
                (
                    "- Normalized output stable: "
                    f"`{item['normalized_match_across_runs']}`"
                ),
                (
                    "- Unique exact answers: "
                    f"`{item['unique_exact_answers']}`"
                ),
                "",
            ]
        )

        for index, answer in enumerate(
            item["answers"],
            start=1,
        ):
            lines.extend(
                [
                    f"Run {index}:",
                    "",
                    "```text",
                    answer,
                    "```",
                    "",
                ]
            )

    lines.extend(
        [
            "## Interpretation",
            "",
            (
                "Temperature was fixed at zero to reduce "
                "sampling variation, but this test does "
                "not assume that local LLM execution is "
                "technically guaranteed to produce "
                "identical text on every run."
            ),
            "",
            (
                "Exact-match differences may include "
                "wording, punctuation, or formatting "
                "changes that do not necessarily change "
                "the semantic answer."
            ),
            "",
            (
                "Normalized comparison is therefore "
                "reported separately from exact-string "
                "comparison."
            ),
            "",
            (
                "Any observed differences should be "
                "reviewed for semantic impact rather than "
                "treated automatically as correctness "
                "failures."
            ),
            "",
            "## Conclusion",
            "",
            (
                "This experiment documents the observed "
                "repeatability of the current Docu AI "
                "answer-generation configuration."
            ),
            "",
            (
                "Reproducibility is evaluated empirically "
                "under controlled settings rather than "
                "assuming guaranteed deterministic output."
            ),
        ]
    )

    REPORT_PATH.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main():
    records, environment = (
        run_experiment()
    )

    write_jsonl(records)

    analysis = analyze(records)

    write_report(
        environment,
        analysis,
    )

    print(
        f"Wrote {RESULTS_PATH}"
    )

    print(
        f"Wrote {REPORT_PATH}"
    )


if __name__ == "__main__":
    main()