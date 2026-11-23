"""
Document-level requests (summaries, "what is this about?", key takeaways)
must not be rejected by the relevance gate, while narrow questions keep the
existing threshold behaviour.
"""

import pytest
from langchain_core.documents import Document

from query_intent import (
    NO_RELEVANT_CONTENT,
    is_document_level_question,
    overview_context,
    representative_chunks,
    retrieve_context,
)


RELEVANCE_THRESHOLD = 0.15
TOP_K = 5


def make_chunks(page_count=10, per_page=2):
    return [
        Document(
            page_content=f"Page {page} part {part} content.",
            metadata={"source": "fixture.pdf", "page": page},
        )
        for page in range(1, page_count + 1)
        for part in range(1, per_page + 1)
    ]


class FakeStore:
    """Returns the given chunks with a fixed relevance score."""

    def __init__(self, results, score):
        self.results = results
        self.score = score
        self.queries = []

    def similarity_search_with_relevance_scores(self, query, k=4):
        self.queries.append((query, k))
        return [(doc, self.score) for doc in self.results[:k]]


@pytest.mark.parametrize(
    "question",
    [
        "give me a summary of the file i uploaded",
        "Summarize this document",
        "summarise the file please",
        "Can you summarize it?",
        "What is this document about?",
        "what's the pdf about",
        "What is it about?",
        "Give me the main points",
        "What are the key takeaways?",
        "key points of this report",
        "tl;dr",
        "Give me an overview",
        "Describe this document",
        "What does this file cover?",
    ],
)
def test_detects_document_level_questions(question):
    assert is_document_level_question(question)


@pytest.mark.parametrize(
    "question",
    [
        "When was the contract signed?",
        "What is the refund policy?",
        "Who is the CEO?",
        "How do we improve activation?",
        "What does Ollama do?",
        "List the pricing tiers",
        "What is the deadline for submissions?",
        "What does the contract say about termination?",
        "What does the report cover regarding pricing in Europe?",
    ],
)
def test_narrow_questions_are_not_document_level(question):
    assert not is_document_level_question(question)


def test_representative_chunks_spread_across_document_in_order():
    chunks = make_chunks(page_count=10, per_page=2)

    picked = representative_chunks(chunks, limit=5)

    assert len(picked) == 5
    assert picked[0] is chunks[0]
    assert picked[-1] is chunks[-1]

    positions = [chunks.index(chunk) for chunk in picked]
    assert positions == sorted(positions)

    pages = {chunk.metadata["page"] for chunk in picked}
    assert len(pages) == 5


def test_representative_chunks_returns_everything_for_short_documents():
    chunks = make_chunks(page_count=2, per_page=1)

    assert representative_chunks(chunks, limit=6) == chunks
    assert representative_chunks([], limit=6) == []


def test_summary_request_passes_even_when_scores_are_below_threshold():
    chunks = make_chunks(page_count=10, per_page=2)
    store = FakeStore(results=[chunks[7]], score=0.02)

    retrieval = retrieve_context(
        "give me a summary of the file i uploaded",
        store,
        chunks,
        top_k=TOP_K,
        relevance_threshold=RELEVANCE_THRESHOLD,
    )

    assert "error" not in retrieval
    assert retrieval["mode"] == "overview"

    results = retrieval["results"]
    pages = [chunk.metadata["page"] for chunk in results]

    # Covers the beginning and the end of the document, in reading order,
    # and keeps source/page metadata for citations.
    assert pages[0] == 1
    assert pages[-1] == 10
    assert pages == sorted(pages)
    assert all(chunk.metadata["source"] == "fixture.pdf" for chunk in results)
    assert len(results) <= 6

    # The best semantic match is still included.
    assert chunks[7] in results


def test_overview_context_has_no_duplicates_when_semantic_hits_overlap():
    chunks = make_chunks(page_count=3, per_page=3)
    store = FakeStore(results=[chunks[0], chunks[-1]], score=0.9)

    results = overview_context("summarize", chunks, store, limit=4)

    identities = [(c.metadata["page"], c.page_content) for c in results]
    assert len(identities) == len(set(identities)) == 4


def test_narrow_question_below_threshold_still_abstains():
    chunks = make_chunks()
    store = FakeStore(results=chunks[:3], score=0.05)

    retrieval = retrieve_context(
        "What is the refund policy?",
        store,
        chunks,
        top_k=TOP_K,
        relevance_threshold=RELEVANCE_THRESHOLD,
    )

    assert retrieval == {"error": NO_RELEVANT_CONTENT}


def test_narrow_question_above_threshold_uses_semantic_results():
    chunks = make_chunks()
    store = FakeStore(results=chunks[4:9], score=0.6)

    retrieval = retrieve_context(
        "How do we improve activation?",
        store,
        chunks,
        top_k=TOP_K,
        relevance_threshold=RELEVANCE_THRESHOLD,
    )

    assert retrieval["mode"] == "focused"
    assert retrieval["results"] == chunks[4:9]
    assert store.queries == [("How do we improve activation?", TOP_K)]
