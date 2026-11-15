from langchain_core.documents import Document


def deduplicate_documents(
    documents: list[Document],
) -> list[Document]:
    """
    Remove only exact duplicate documents.

    A document is considered a duplicate only when
    page content, source, and page number are all
    identical.

    Identical text from different pages or different
    source documents must be preserved.
    """
    seen = set()
    unique_documents = []

    for document in documents:
        key = (
            document.page_content,
            document.metadata.get("source"),
            document.metadata.get("page"),
        )

        if key in seen:
            continue

        seen.add(key)
        unique_documents.append(document)

    return unique_documents