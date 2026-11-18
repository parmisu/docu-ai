import json
from pathlib import Path

from ollama_error_handling import (
    invoke_ollama_safely,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "error_scenarios.json"
)


def load_fixture():
    return json.loads(
        FIXTURE_PATH.read_text(
            encoding="utf-8"
        )
    )


class FailingModel:
    def __init__(
        self,
        exception,
    ):
        self.exception = exception

    def invoke(
        self,
        messages,
    ):
        raise self.exception


class SuccessfulResponse:
    def __init__(
        self,
        content,
    ):
        self.content = content


class SuccessfulModel:
    def invoke(
        self,
        messages,
    ):
        return SuccessfulResponse(
            "Controlled successful answer."
        )


def build_exception(
    exception_type,
    raw_error,
):
    mapping = {
        "ConnectionError": (
            ConnectionError
        ),
        "TimeoutError": (
            TimeoutError
        ),
        "RuntimeError": (
            RuntimeError
        ),
    }

    exception_class = mapping[
        exception_type
    ]

    return exception_class(
        raw_error
    )


def test_connection_failures_are_handled():
    fixture = load_fixture()

    for scenario in fixture[
        "scenarios"
    ]:
        exception = build_exception(
            scenario[
                "exception_type"
            ],
            scenario[
                "raw_error"
            ],
        )

        model = FailingModel(
            exception
        )

        result = (
            invoke_ollama_safely(
                model,
                ["test message"],
            )
        )

        assert result["ok"] is False

        assert (
            result["content"]
            is None
        )

        assert (
            result["error_type"]
            == scenario[
                "expected_error_type"
            ]
        )

        assert result[
            "user_message"
        ]


def test_raw_exception_is_not_exposed_to_user():
    fixture = load_fixture()

    for scenario in fixture[
        "scenarios"
    ]:
        exception = build_exception(
            scenario[
                "exception_type"
            ],
            scenario[
                "raw_error"
            ],
        )

        result = (
            invoke_ollama_safely(
                FailingModel(
                    exception
                ),
                ["test message"],
            )
        )

        user_message = result[
            "user_message"
        ]

        assert (
            scenario["raw_error"]
            not in user_message
        )

        assert (
            "traceback"
            not in user_message.lower()
        )

        assert (
            "localhost:11434"
            not in user_message
        )


def test_failure_does_not_leave_answer_content():
    model = FailingModel(
        ConnectionError(
            "Connection refused"
        )
    )

    result = (
        invoke_ollama_safely(
            model,
            ["question"],
        )
    )

    assert result == {
        "ok": False,
        "content": None,
        "user_message": (
    "Ollama could not be reached. Make sure the "
    "Ollama service is running and try again."
),
        "error_type": (
            "connection_error"
        ),
    }


def test_success_state_remains_valid():
    model = SuccessfulModel()

    result = (
        invoke_ollama_safely(
            model,
            ["question"],
        )
    )

    assert result["ok"] is True

    assert (
        result["content"]
        == "Controlled successful answer."
    )

    assert (
        result["user_message"]
        is None
    )

    assert (
        result["error_type"]
        is None
    )


def test_fixture_defines_failure_scenarios():
    fixture = load_fixture()

    assert len(
        fixture["scenarios"]
    ) >= 3

    for scenario in fixture[
        "scenarios"
    ]:
        assert scenario["id"]

        assert scenario[
            "raw_error"
        ]

        assert scenario[
            "expected_error_type"
        ]