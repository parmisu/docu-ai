from dataclasses import dataclass
from typing import Optional


@dataclass
class AppDocumentState:
    active_document_key: Optional[str] = None
    active_document_name: Optional[str] = None

    pending_document_key: Optional[str] = None
    pending_document_name: Optional[str] = None

    status: str = "empty"
    error_message: Optional[str] = None


def begin_processing(
    state,
    document_key,
    document_name,
):
    state.pending_document_key = (
        document_key
    )

    state.pending_document_name = (
        document_name
    )

    state.status = "processing"
    state.error_message = None


def processing_succeeded(
    state,
):
    if (
        state.pending_document_key
        is None
    ):
        raise ValueError(
            "No pending document exists."
        )

    state.active_document_key = (
        state.pending_document_key
    )

    state.active_document_name = (
        state.pending_document_name
    )

    state.pending_document_key = None
    state.pending_document_name = None

    state.status = "ready"
    state.error_message = None


def processing_failed(
    state,
    user_message,
):
    state.pending_document_key = None
    state.pending_document_name = None

    state.status = (
        "ready"
        if state.active_document_key
        else "error"
    )

    state.error_message = (
        user_message
    )


def clear_document(
    state,
):
    state.active_document_key = None
    state.active_document_name = None

    state.pending_document_key = None
    state.pending_document_name = None

    state.status = "empty"
    state.error_message = None


def can_answer_questions(
    state,
):
    return (
        state.status == "ready"
        and state.active_document_key
        is not None
    )