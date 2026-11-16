# Irrelevant Retrieval Evaluation

## Purpose

This evaluation checks how Docu AI behaves when a question has no supported answer in the indexed document.

A retrieved result is not treated as evidence
solely because similarity search returned it.

## Relevance Threshold

`0.15`

## Results

### Question: ChromaDB stores vector embeddings for semantic retrieval. What is its monthly price?

- Best score: `0.661953`
- Evidence found: `False`
- Decision: `UNSUPPORTED`

| Rank | Page | Score | Evidence | Text |
|---:|---:|---:|---|---|
| 1 | 2 | 0.661953 | False | CHROMA_MARKER ChromaDB stores vector embeddings for semantic retrieval. |
| 2 | 3 | -0.008518 | False | OLLAMA_MARKER Ollama runs the local language model used to generate answers. |
| 3 | 5 | -0.101126 | False | SOURCE_MARKER Retrieved chunks retain source names and page numbers for traceability. |
| 4 | 1 | -0.123088 | False | PYTHON_MARKER Python handles document processing and application logic in Docu AI. |
| 5 | 4 | -0.19658 | False | STREAMLIT_MARKER Streamlit provides the interface for uploading PDFs and asking questions. |

### Question: Who founded Streamlit?

- Best score: `0.004074`
- Evidence found: `False`
- Decision: `UNSUPPORTED`

| Rank | Page | Score | Evidence | Text |
|---:|---:|---:|---|---|
| 1 | 4 | 0.004074 | False | STREAMLIT_MARKER Streamlit provides the interface for uploading PDFs and asking questions. |
| 2 | 5 | -0.272862 | False | SOURCE_MARKER Retrieved chunks retain source names and page numbers for traceability. |
| 3 | 3 | -0.34299 | False | OLLAMA_MARKER Ollama runs the local language model used to generate answers. |
| 4 | 1 | -0.438198 | False | PYTHON_MARKER Python handles document processing and application logic in Docu AI. |
| 5 | 2 | -0.460047 | False | CHROMA_MARKER ChromaDB stores vector embeddings for semantic retrieval. |

### Question: What will the weather be tomorrow?

- Best score: `-0.303602`
- Evidence found: `False`
- Decision: `UNSUPPORTED`

| Rank | Page | Score | Evidence | Text |
|---:|---:|---:|---|---|
| 1 | 3 | -0.303602 | False | OLLAMA_MARKER Ollama runs the local language model used to generate answers. |
| 2 | 4 | -0.377138 | False | STREAMLIT_MARKER Streamlit provides the interface for uploading PDFs and asking questions. |
| 3 | 1 | -0.431105 | False | PYTHON_MARKER Python handles document processing and application logic in Docu AI. |
| 4 | 2 | -0.439308 | False | CHROMA_MARKER ChromaDB stores vector embeddings for semantic retrieval. |
| 5 | 5 | -0.468275 | False | SOURCE_MARKER Retrieved chunks retain source names and page numbers for traceability. |

## Interpretation

Similarity alone is not sufficient to establish that the document contains a valid answer.

A result may be semantically close to the question while still lacking the specific evidence needed to answer it.