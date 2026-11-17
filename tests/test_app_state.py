from app_state import (
    AppDocumentState,
    begin_processing,
    can_answer_questions,
    clear_document,
    processing_failed,
    processing_succeeded,
)


def test_initial_state_is_empty():
    state = AppDocumentState()

    assert state.status == "empty"
    assert (
        state.active_document_key
        is None
    )

    assert (
        can_answer_questions(
            state
        )
        is False
    )


def test_successful_upload_becomes_active():
    state = AppDocumentState()

    begin_processing(
        state,
        "hash-a",
        "document_a.pdf",
    )

    assert (
        state.status
        == "processing"
    )

    assert (
        state.active_document_name
        is None
    )

    processing_succeeded(
        state
    )

    assert (
        state.status
        == "ready"
    )

    assert (
        state.active_document_key
        == "hash-a"
    )

    assert (
        state.active_document_name
        == "document_a.pdf"
    )

    assert (
        can_answer_questions(
            state
        )
        is True
    )


def test_failed_new_upload_does_not_replace_previous_document():
    state = AppDocumentState()

    begin_processing(
        state,
        "hash-a",
        "document_a.pdf",
    )

    processing_succeeded(
        state
    )

    begin_processing(
        state,
        "hash-b",
        "document_b.pdf",
    )

    assert (
        state.pending_document_name
        == "document_b.pdf"
    )

    assert (
        state.active_document_name
        == "document_a.pdf"
    )

    processing_failed(
        state,
        "Document B could not be processed.",
    )

    assert (
        state.active_document_name
        == "document_a.pdf"
    )

    assert (
        state.active_document_key
        == "hash-a"
    )

    assert (
        state.status
        == "ready"
    )

    assert (
        state.error_message
        == (
            "Document B could not "
            "be processed."
        )
    )


def test_failed_first_upload_does_not_create_ready_document():
    state = AppDocumentState()

    begin_processing(
        state,
        "bad-hash",
        "broken.pdf",
    )

    processing_failed(
        state,
        "The PDF could not be processed.",
    )

    assert (
        state.active_document_key
        is None
    )

    assert (
        state.active_document_name
        is None
    )

    assert (
        state.status
        == "error"
    )

    assert (
        can_answer_questions(
            state
        )
        is False
    )


def test_retry_after_failure_can_succeed():
    state = AppDocumentState()

    begin_processing(
        state,
        "hash-b",
        "document_b.pdf",
    )

    processing_failed(
        state,
        "Temporary processing error.",
    )

    assert (
        can_answer_questions(
            state
        )
        is False
    )

    begin_processing(
        state,
        "hash-b",
        "document_b.pdf",
    )

    processing_succeeded(
        state
    )

    assert (
        state.active_document_name
        == "document_b.pdf"
    )

    assert (
        state.status
        == "ready"
    )

    assert (
        state.error_message
        is None
    )

    assert (
        can_answer_questions(
            state
        )
        is True
    )


def test_rerun_preserves_valid_ready_state():
    state = AppDocumentState(
        active_document_key="hash-a",
        active_document_name=(
            "document_a.pdf"
        ),
        status="ready",
    )

    assert (
        state.active_document_name
        == "document_a.pdf"
    )

    assert (
        can_answer_questions(
            state
        )
        is True
    )


def test_processing_state_is_not_treated_as_ready():
    state = AppDocumentState()

    begin_processing(
        state,
        "hash-a",
        "document_a.pdf",
    )

    assert (
        state.status
        == "processing"
    )

    assert (
        can_answer_questions(
            state
        )
        is False
    )


def test_clear_document_removes_active_state():
    state = AppDocumentState(
        active_document_key="hash-a",
        active_document_name=(
            "document_a.pdf"
        ),
        status="ready",
    )

    clear_document(
        state
    )

    assert (
        state.status
        == "empty"
    )

    assert (
        state.active_document_key
        is None
    )

    assert (
        state.active_document_name
        is None
    )

    assert (
        can_answer_questions(
            state
        )
        is False
    )