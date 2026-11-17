import json
from pathlib import Path

from input_validation import (
    MAX_QUESTION_LENGTH,
    validate_question,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "input-validation-cases.json"
)


def load_fixture():
    return json.loads(
        FIXTURE_PATH.read_text(
            encoding="utf-8"
        )
    )


class CountingModel:
    def __init__(self):
        self.calls = 0

    def invoke(self, messages):
        self.calls += 1

        return "MODEL_CALLED"


def process_question(
    question,
    model,
):
    validation = validate_question(
        question
    )

    if not validation["valid"]:
        return {
            "model_called": False,
            "message": validation[
                "message"
            ],
            "error_type": validation[
                "error_type"
            ],
        }

    model.invoke(
        [
            validation[
                "clean_question"
            ]
        ]
    )

    return {
        "model_called": True,
        "message": None,
        "error_type": None,
    }


def test_fixture_matches_validation_policy():
    fixture = load_fixture()

    assert (
        fixture["max_question_length"]
        == MAX_QUESTION_LENGTH
    )

    assert (
        fixture["language_scope"]
        == "English"
    )


def test_empty_input_is_rejected():
    result = validate_question(
        ""
    )

    assert result["valid"] is False
    assert (
        result["error_type"]
        == "empty_input"
    )

    assert result["message"]


def test_whitespace_only_input_is_rejected():
    result = validate_question(
        "       "
    )

    assert result["valid"] is False

    assert (
        result["error_type"]
        == "empty_input"
    )


def test_valid_question_is_trimmed():
    result = validate_question(
        "   What stores embeddings?   "
    )

    assert result["valid"] is True

    assert (
        result["clean_question"]
        == "What stores embeddings?"
    )


def test_exact_length_boundary_is_allowed():
    question = (
        "A"
        * MAX_QUESTION_LENGTH
    )

    result = validate_question(
        question
    )

    assert result["valid"] is True

    assert (
        len(
            result[
                "clean_question"
            ]
        )
        == MAX_QUESTION_LENGTH
    )


def test_over_length_boundary_is_rejected():
    question = (
        "A"
        * (
            MAX_QUESTION_LENGTH
            + 1
        )
    )

    result = validate_question(
        question
    )

    assert result["valid"] is False

    assert (
        result["error_type"]
        == "too_long"
    )

    assert (
        "500"
        in result["message"]
    )


def test_invalid_input_does_not_call_model():
    model = CountingModel()

    result = process_question(
        "     ",
        model,
    )

    assert (
        result["model_called"]
        is False
    )

    assert model.calls == 0


def test_overlong_input_does_not_call_model():
    model = CountingModel()

    question = (
        "A"
        * (
            MAX_QUESTION_LENGTH
            + 1
        )
    )

    result = process_question(
        question,
        model,
    )

    assert (
        result["model_called"]
        is False
    )

    assert model.calls == 0


def test_valid_input_calls_model_once():
    model = CountingModel()

    result = process_question(
        "What is ChromaDB?",
        model,
    )

    assert (
        result["model_called"]
        is True
    )

    assert model.calls == 1


def test_non_english_like_input_is_rejected():
    result = validate_question(
        "۱۲۳۴۵۶"
    )

    assert result["valid"] is False

    assert (
        result["error_type"]
        == "unsupported_language"
    )

    assert (
        "English"
        in result["message"]
    )