def invoke_ollama_safely(
    model,
    messages,
):
    """
    Safely invoke an Ollama-compatible chat model.

    Returns a controlled result dictionary and prevents
    model/service failures from appearing as valid answers.
    """
    try:
        response = model.invoke(messages)

        content = getattr(
            response,
            "content",
            None,
        )

        if not isinstance(
            content,
            str,
        ):
            return {
                "ok": False,
                "content": None,
                "user_message": (
                    "The local AI model returned an invalid "
                    "response. Please try again. If the problem "
                    "continues, restart Ollama."
                ),
                "error_type": (
                    "invalid_response"
                ),
            }

        content = content.strip()

        if not content:
            return {
                "ok": False,
                "content": None,
                "user_message": (
                    "The local AI model returned an empty "
                    "response. Please try again. If the problem "
                    "continues, restart Ollama."
                ),
                "error_type": (
                    "invalid_response"
                ),
            }

        return {
            "ok": True,
            "content": content,
            "user_message": None,
            "error_type": None,
        }

    except Exception as exc:
        error_text = str(
            exc
        ).lower()

        if (
            "model" in error_text
            and (
                "not found" in error_text
                or "missing" in error_text
                or "does not exist" in error_text
            )
        ):
            return {
                "ok": False,
                "content": None,
                "user_message": (
                    "The required Ollama model is not installed. "
                    "Run `ollama pull llama3.2:3b` and try again."
                ),
                "error_type": (
                    "model_not_found"
                ),
            }

        if isinstance(
            exc,
            TimeoutError,
        ) or "timeout" in error_text or (
            "timed out" in error_text
        ):
            return {
                "ok": False,
                "content": None,
                "user_message": (
                    "The local AI model took too long to respond. "
                    "Please try again. If the timeout continues, "
                    "restart Ollama or use a smaller document."
                ),
                "error_type": (
                    "timeout"
                ),
            }

        if isinstance(
            exc,
            ConnectionError,
        ) or (
            "connection refused"
            in error_text
        ):
            return {
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

        return {
            "ok": False,
            "content": None,
            "user_message": (
                "The local AI service encountered an error. "
                "Please try again. If the problem continues, "
                "restart Ollama."
            ),
            "error_type": (
                "service_error"
            ),
        }