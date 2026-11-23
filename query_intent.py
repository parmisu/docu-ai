"""
Retrieval routing for DocuAI.

Most questions are narrow lookups ("When was the contract signed?") and are
answered from the top semantic matches, guarded by a relevance threshold so
unrelated questions abstain instead of hallucinating.

Document-level requests ("summarize this file", "what is this about?",
"key takeaways") are different: no single chunk is "relevant" to them, so a
similarity threshold rejects them even though the document obviously can
answer. For those we build an overview context instead: a few chunks sampled
evenly across the whole document, plus the best semantic matches, in reading
order. Answers stay grounded in the uploaded document and every chunk keeps
its source/page metadata for citations.
"""

from __future__ import annotations

import re
from typing import Any, Protocol, Sequence

from langchain_core.documents import Document


OVERVIEW_CHUNK_LIMIT = 6
OVERVIEW_SEMANTIC_CHUNKS = 2

NO_RELEVANT_CONTENT = (
    "I couldn't find anything relevant "
    "to that question in this document."
)

_DOCUMENT_NOUN = (
    r"(?:document|doc|file|pdf|paper|report|text|article|"
    r"upload|attachment|contents?)"
)

_DOCUMENT_LEVEL_PATTERNS = [
    # summarize / summary / summarise / tl;dr / recap / overview / gist
    r"\bsummar(?:y|ies|ise|ize|ised|ized|ising|izing|isation|ization)\b",
    r"\btl\s*;?\s*dr\b",
    r"\b(?:overview|recap|synopsis|gist|abstract)\b",
    # what is this document about / what's the file about
    rf"\bwhat(?:'s|\s+is|\s+are)?\s+(?:this|the|that|my|it)\s*"
    rf"(?:{_DOCUMENT_NOUN})?\s*(?:all\s+)?about\b",
    rf"\bwhat\s+(?:does|do)\s+(?:this|the|it|that|my)\s*"
    rf"(?:{_DOCUMENT_NOUN})?\s*(?:cover|say|discuss|contain)\s*[?.!]*\s*$",
    # main points / key takeaways / important ideas
    r"\b(?:main|key|important|core|central|major|primary)\s+"
    r"(?:points?|ideas?|takeaways?|themes?|topics?|findings?|messages?|"
    r"arguments?|highlights?|conclusions?|insights?)\b",
    r"\btake\s*-?\s*aways?\b",
    r"\bhighlights\b",
    # describe / explain / outline the document
    rf"\b(?:describe|explain|outline|break\s+down)\s+(?:this|the|my)\s+"
    rf"{_DOCUMENT_NOUN}\b",
]

_DOCUMENT_LEVEL_RE = re.compile(
    "|".join(f"(?:{pattern})" for pattern in _DOCUMENT_LEVEL_PATTERNS),
    re.IGNORECASE,
)


class SupportsRelevanceSearch(Protocol):
    def similarity_search_with_relevance_scores(
        self,
        query: str,
        k: int = ...,
    ) -> list[tuple[Document, float]]:
        ...


def is_document_level_question(
    question: str,
) -> bool:
    """True for broad requests about the whole document (summary, gist...)."""

    normalized = " ".join(question.replace("’", "'").split())

    return bool(_DOCUMENT_LEVEL_RE.search(normalized))


def _chunk_identity(
    chunk: Document,
) -> tuple[Any, Any, str]:
    return (
        chunk.metadata.get("source"),
        chunk.metadata.get("page"),
        chunk.page_content,
    )


def representative_chunks(
    chunks: Sequence[Document],
    limit: int = OVERVIEW_CHUNK_LIMIT,
) -> list[Document]:
    """
    Pick up to `limit` chunks spread evenly across the document, always
    including the first and last chunk, returned in reading order.
    `chunks` must already be in reading order (as produced by the splitter).
    """

    if limit <= 0 or not chunks:
        return []

    if len(chunks) <= limit:
        return list(chunks)

    if limit == 1:
        return [chunks[0]]

    last = len(chunks) - 1
    indices = sorted(
        {round(step * last / (limit - 1)) for step in range(limit)}
    )

    return [chunks[index] for index in indices]


def overview_context(
    question: str,
    chunks: Sequence[Document],
    vector_store: SupportsRelevanceSearch,
    limit: int = OVERVIEW_CHUNK_LIMIT,
    semantic_chunks: int = OVERVIEW_SEMANTIC_CHUNKS,
) -> list[Document]:
    """
    Context for a document-level request: the best semantic matches (so
    "summarize the pricing section" still focuses on pricing) topped up with
    chunks sampled across the document, deduplicated, in reading order.
    """

    order = {
        _chunk_identity(chunk): index
        for index, chunk in enumerate(chunks)
    }

    selected: dict[tuple[Any, Any, str], Document] = {}

    if semantic_chunks > 0:
        for document, _score in (
            vector_store.similarity_search_with_relevance_scores(
                question,
                k=semantic_chunks,
            )
        ):
            selected.setdefault(_chunk_identity(document), document)

    # Spread the remaining slots over the whole document (first and last
    # chunk included); if that overlapped the semantic picks, top up again.
    for spread_size in (limit - len(selected), limit):
        for chunk in representative_chunks(chunks, spread_size):
            if len(selected) >= limit:
                break
            selected.setdefault(_chunk_identity(chunk), chunk)

    return sorted(
        selected.values(),
        key=lambda chunk: order.get(_chunk_identity(chunk), len(order)),
    )


def retrieve_context(
    question: str,
    vector_store: SupportsRelevanceSearch,
    chunks: Sequence[Document],
    top_k: int,
    relevance_threshold: float,
) -> dict:
    """
    Decide how to gather context for `question`.

    Returns {"mode": "overview" | "focused", "results": [Document, ...]}
    or {"error": message} when a focused question has no relevant match.
    """

    if is_document_level_question(question) and chunks:
        return {
            "mode": "overview",
            "results": overview_context(question, chunks, vector_store),
        }

    scored_results = vector_store.similarity_search_with_relevance_scores(
        question,
        k=top_k,
    )

    if (
        not scored_results
        or scored_results[0][1] < relevance_threshold
    ):
        return {"error": NO_RELEVANT_CONTENT}

    return {
        "mode": "focused",
        "results": [document for document, _score in scored_results],
    }
