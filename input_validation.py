MAX_QUESTION_LENGTH = 500


def validate_question(question):
    """
    Validate a user question before retrieval or
    model execution.

    Current project scope:
    - English questions
    - Maximum 500 characters
    """

    if question is None:
        return {
            "valid": False,
            "clean_question": "",
            "message": (
                "Please enter a question."
            ),
            "error_type": "empty_input",
        }

    clean_question = question.strip()

    if not clean_question:
        return {
            "valid": False,
            "clean_question": "",
            "message": (
                "Please enter a question."
            ),
            "error_type": "empty_input",
        }

    if len(clean_question) > MAX_QUESTION_LENGTH:
        return {
            "valid": False,
            "clean_question": clean_question,
            "message": (
                "Your question is too long. "
                "Please keep it under 500 characters."
            ),
            "error_type": "too_long",
        }

    if not any(
        char.isascii() and char.isalpha()
        for char in clean_question
    ):
        return {
            "valid": False,
            "clean_question": clean_question,
            "message": (
                "Please enter your question in English."
            ),
            "error_type": "unsupported_language",
        }

    return {
        "valid": True,
        "clean_question": clean_question,
        "message": None,
        "error_type": None,
    }