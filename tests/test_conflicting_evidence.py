import json
from pathlib import Path
from uuid import uuid4

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama


ROOT = Path(__file__).parent.parent

FIXTURE_DIR = (
    ROOT
    / "tests"
    / "fixtures"
    / "conflicting_documents"
)

REPORT_PATH = (
    ROOT
    / "evaluation"
    / "conflict-report.md"
)

TOP_K = 2


def load_documents():
    documents = []

    files = [
        (
            "source_a.txt",
            1,
        ),
        (
            "source_b.txt",
            1,
        ),
    ]

    for file_name, page in files:
        path = FIXTURE_DIR / file_name

        documents.append(
            Document(
                page_content=path.read_text(
                    encoding="utf-8"
                ).strip(),
                metadata={
                    "source": file_name,
                    "page": page,
                },
            )
        )

    return documents


def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=(
            "sentence-transformers/"
            "all-MiniLM-L6-v2"
        )
    )


def build_vector_store():
    return Chroma.from_documents(
        documents=load_documents(),
        embedding=get_embeddings(),
        collection_name=(
            f"conflict_test_{uuid4().hex}"
        ),
    )


def retrieve_conflicting_sources():
    vector_store = build_vector_store()

    return (
        vector_store
        .similarity_search_with_relevance_scores(
            "What is the Nova protocol timeout?",
            k=TOP_K,
        )
    )


def generate_conflict_answer(results):
    context_parts = []

    for document, score in results:
        context_parts.append(
            (
                f"Source: "
                f"{document.metadata['source']}\n"
                f"Page: "
                f"{document.metadata['page']}\n"
                f"Content: "
                f"{document.page_content}"
            )
        )

    context = "\n\n".join(
        context_parts
    )

    model = ChatOllama(
        model="llama3.2:3b",
        temperature=0,
    )

    prompt = f"""
Use only the supplied sources.

The sources may disagree.

If the sources contain conflicting facts:
- explicitly state that there is a conflict
- describe both claims
- identify which source supports each claim
- do not choose one claim as definitively true
  unless the supplied evidence resolves the conflict

Question:
What is the Nova protocol timeout?

Sources:
{context}

Answer:
"""

    response = model.invoke(
        [
            HumanMessage(
                content=prompt
            )
        ]
    )

    return response.content.strip()


def answer_acknowledges_conflict(answer):
    normalized = answer.lower()

    conflict_terms = [
        "conflict",
        "conflicting",
        "disagree",
        "disagreement",
        "different",
        "inconsistent",
    ]

    return any(
        term in normalized
        for term in conflict_terms
    )


def answer_preserves_both_claims(answer):
    normalized = answer.lower()

    return (
        "30" in normalized
        and "60" in normalized
    )


def answer_mentions_both_sources(answer):
    normalized = answer.lower()

    return (
        "source_a" in normalized
        or "source a" in normalized
    ) and (
        "source_b" in normalized
        or "source b" in normalized
    )


def write_report(
    results,
    answer,
    conflict_acknowledged,
    both_claims_present,
    both_sources_present,
):
    lines = [
        "# Conflicting Evidence Evaluation",
        "",
        "## Purpose",
        "",
        (
            "This evaluation tests whether Docu AI "
            "handles contradictory source evidence "
            "without presenting one unsupported claim "
            "as definitive truth."
        ),
        "",
        "## Retrieved Evidence",
        "",
    ]

    for rank, (
        document,
        score,
    ) in enumerate(
        results,
        start=1,
    ):
        lines.extend(
            [
                f"### Rank {rank}",
                "",
                (
                    f"- Source: "
                    f"`{document.metadata['source']}`"
                ),
                (
                    f"- Page: "
                    f"`{document.metadata['page']}`"
                ),
                (
                    f"- Score: "
                    f"`{round(float(score), 6)}`"
                ),
                "",
                document.page_content,
                "",
            ]
        )

    lines.extend(
        [
            "## Model Answer",
            "",
            answer,
            "",
            "## Evaluation",
            "",
            (
                "- Conflict acknowledged: "
                f"`{conflict_acknowledged}`"
            ),
            (
                "- Both conflicting claims preserved: "
                f"`{both_claims_present}`"
            ),
            (
                "- Both sources identified: "
                f"`{both_sources_present}`"
            ),
            "",
            "## Expected Policy",
            "",
            (
                "When retrieved sources disagree, the "
                "system must expose the disagreement "
                "or state that the evidence is "
                "insufficient to resolve it."
            ),
            "",
            (
                "It must not select one conflicting "
                "claim as definitive truth without "
                "supporting evidence that resolves "
                "the conflict."
            ),
        ]
    )

    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_PATH.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def test_both_conflicting_sources_are_retrieved():
    results = retrieve_conflicting_sources()

    assert len(results) == 2

    combined = " ".join(
        document.page_content
        for document, _ in results
    )

    sources = {
        document.metadata["source"]
        for document, _ in results
    }

    assert "30 seconds" in combined
    assert "60 seconds" in combined

    assert sources == {
        "source_a.txt",
        "source_b.txt",
    }


def test_model_reports_conflict_without_resolving_it():
    results = retrieve_conflicting_sources()

    answer = generate_conflict_answer(
        results
    )

    conflict_acknowledged = (
        answer_acknowledges_conflict(
            answer
        )
    )

    both_claims_present = (
        answer_preserves_both_claims(
            answer
        )
    )

    both_sources_present = (
        answer_mentions_both_sources(
            answer
        )
    )

    write_report(
        results,
        answer,
        conflict_acknowledged,
        both_claims_present,
        both_sources_present,
    )

    assert conflict_acknowledged
    assert both_claims_present
    assert both_sources_present


def test_fixture_contains_real_conflict():
    source_a = (
        FIXTURE_DIR
        / "source_a.txt"
    ).read_text(
        encoding="utf-8"
    )

    source_b = (
        FIXTURE_DIR
        / "source_b.txt"
    ).read_text(
        encoding="utf-8"
    )

    assert "30 seconds" in source_a
    assert "60 seconds" in source_b

    assert source_a != source_b