import os
from pathlib import Path

import pytest


OLLAMA_INTEGRATION_FILES = {
    "test_answer_generation.py",
    "test_abstention.py",
    "test_conflicting_evidence.py",
}


def pytest_collection_modifyitems(
    config,
    items,
):
    run_ollama_tests = (
        os.getenv(
            "RUN_OLLAMA_TESTS"
        )
        == "1"
    )

    ollama_skip = pytest.mark.skip(
        reason=(
            "requires a real local Ollama "
            "service and model; run with "
            "RUN_OLLAMA_TESTS=1"
        )
    )

    for item in items:
        file_name = Path(
            str(item.fspath)
        ).name

        if (
            file_name
            in OLLAMA_INTEGRATION_FILES
        ):
            item.add_marker(
                pytest.mark.integration
            )

            if not run_ollama_tests:
                item.add_marker(
                    ollama_skip
                )