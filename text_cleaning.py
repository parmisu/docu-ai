import re


def clean_extracted_text(text: str) -> str:
    """
    Normalize harmless whitespace and replacement characters
    without removing meaningful content.
    """
    if not text:
        return ""

    cleaned = text.replace("\ufffd", " ")

    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"[ \t]*\n[ \t]*", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()