import json
from pathlib import Path

from text_cleaning import clean_extracted_text


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "expected_text"
    / "edge_cases.json"
)


def load_cases():
    data = json.loads(
        FIXTURE_PATH.read_text(encoding="utf-8")
    )

    return data["cases"]


def test_extraction_edge_cases():
    for case in load_cases():
        result = clean_extracted_text(
            case["input"]
        )

        assert result == case["expected"], (
            f"Failed case: {case['name']}"
        )


def test_essential_content_is_preserved():
    original = (
        "Python 3.11, ChromaDB, Ollama, "
        "and Streamlit."
    )

    cleaned = clean_extracted_text(original)

    for essential_term in [
        "Python 3.11",
        "ChromaDB",
        "Ollama",
        "Streamlit",
    ]:
        assert essential_term in cleaned