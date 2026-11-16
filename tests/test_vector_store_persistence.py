import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parent.parent
APP_PATH = ROOT / "app.py"

COLLECTION_NAME = "persistence_restart_test"


WORKER_CODE = r'''
import sys

from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document


class TestEmbeddings(Embeddings):
    def embed_documents(self, texts):
        return [
            self._vector(text)
            for text in texts
        ]

    def embed_query(self, text):
        return self._vector(text)

    @staticmethod
    def _vector(text):
        value = float(
            sum(ord(char) for char in text) % 1000
        ) / 1000.0

        return [
            value,
            value / 2.0,
            1.0 - value,
        ]


mode = sys.argv[1]
collection_name = sys.argv[2]

store = Chroma(
    collection_name=collection_name,
    embedding_function=TestEmbeddings(),
)

if mode == "write":
    store.add_documents(
        [
            Document(
                page_content=(
                    "PERSISTENCE_MARKER "
                    "This record belongs to the first run."
                ),
                metadata={
                    "source": "persistence_fixture.pdf",
                    "page": 1,
                },
            )
        ]
    )

stored = store.get()

print(len(stored["ids"]))
'''


def run_worker(mode):
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            WORKER_CODE,
            mode,
            COLLECTION_NAME,
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output_lines = [
        line.strip()
        for line in completed.stdout.splitlines()
        if line.strip()
    ]

    return int(output_lines[-1])


def test_first_process_can_store_record():
    count = run_worker("write")

    assert count == 1


def test_new_process_does_not_recover_previous_store():
    first_run_count = run_worker(
        "write"
    )

    second_run_count = run_worker(
        "read"
    )

    assert first_run_count == 1
    assert second_run_count == 0


def test_current_app_has_no_persistent_directory():
    app_source = APP_PATH.read_text(
        encoding="utf-8"
    )

    persistent_config = re.search(
        r"persist_directory\s*=",
        app_source,
    )

    assert persistent_config is None