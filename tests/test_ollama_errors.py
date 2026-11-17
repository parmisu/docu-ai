from ollama_error_handling import (
    invoke_ollama_safely,
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


class Response:
    def __init__(
        self,
        content,
    ):
        self.content = content


class ResponseModel:
    def __init__(
        self,
        content,
    ):
        self.content = content

    def invoke(
        self,
        messages,
    ):
        return Response(
            self.content
        )


def test_missing_model_is_explained():
    model = FailingModel(
        RuntimeError(
            "model llama3.2:3b not found"
        )
    )

    result = (
        invoke_ollama_safely(
            model,
            ["question"],
        )
    )

    assert result["ok"] is False
    assert result["content"] is None

    assert (
        result["error_type"]
        == "model_not_found"
    )

    assert (
        "not installed"
        in result[
            "user_message"
        ].lower()
    )

    assert (
        "ollama pull llama3.2:3b"
        in result[
            "user_message"
        ].lower()
    )


def test_timeout_explains_next_action():
    model = FailingModel(
        TimeoutError(
            "Request timed out"
        )
    )

    result = (
        invoke_ollama_safely(
            model,
            ["question"],
        )
    )

    assert result["ok"] is False
    assert result["content"] is None

    assert (
        result["error_type"]
        == "timeout"
    )

    assert (
        "too long"
        in result[
            "user_message"
        ].lower()
    )

    assert (
        "try again"
        in result[
            "user_message"
        ].lower()
    )


def test_invalid_none_response_is_rejected():
    model = ResponseModel(
        None
    )

    result = (
        invoke_ollama_safely(
            model,
            ["question"],
        )
    )

    assert result["ok"] is False
    assert result["content"] is None

    assert (
        result["error_type"]
        == "invalid_response"
    )

    assert (
        "invalid response"
        in result[
            "user_message"
        ].lower()
    )


def test_empty_response_is_rejected():
    model = ResponseModel(
        "   "
    )

    result = (
        invoke_ollama_safely(
            model,
            ["question"],
        )
    )

    assert result["ok"] is False
    assert result["content"] is None

    assert (
        result["error_type"]
        == "invalid_response"
    )


def test_service_error_is_controlled():
    model = FailingModel(
        RuntimeError(
            "Internal Ollama server error"
        )
    )

    result = (
        invoke_ollama_safely(
            model,
            ["question"],
        )
    )

    assert result["ok"] is False
    assert result["content"] is None

    assert (
        result["error_type"]
        == "service_error"
    )

    assert (
        "service"
        in result[
            "user_message"
        ].lower()
    )

    assert (
        "restart ollama"
        in result[
            "user_message"
        ].lower()
    )


def test_connection_error_remains_controlled():
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

    assert result["ok"] is False
    assert result["content"] is None

    assert (
        result["error_type"]
        == "connection_error"
    )

    assert (
        "make sure"
        in result[
            "user_message"
        ].lower()
    )


def test_failure_never_becomes_valid_answer():
    scenarios = [
        FailingModel(
            RuntimeError(
                "model llama3.2:3b not found"
            )
        ),
        FailingModel(
            TimeoutError(
                "timed out"
            )
        ),
        FailingModel(
            RuntimeError(
                "server failure"
            )
        ),
        ResponseModel(None),
        ResponseModel(""),
    ]

    for model in scenarios:
        result = (
            invoke_ollama_safely(
                model,
                ["question"],
            )
        )

        assert result["ok"] is False
        assert result["content"] is None
        assert result["user_message"]
        assert result["error_type"]