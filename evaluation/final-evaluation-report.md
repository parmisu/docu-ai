# Final Answer Evaluation Report

## Purpose

This evaluation measures answer correctness, citation coverage, and abstention behavior using the fixed reference dataset.

## Evaluation Method

### Answer Correctness

Answerable cases are compared with the human-defined reference answer using normalized meaningful-token recall.

A case passes the automated answer-correctness check when reference token recall is at least `0.50`.

Exact string equality is not required.

Conflict cases additionally require the answer to acknowledge disagreement and preserve both 30-second and 60-second claims.

### Citation Accuracy

Expected citations are evaluated against the human-defined source, page, and evidence marker.

A citation case is fully correct only when all expected evidence sections appear within the top-five retrieved results.

### Abstention

Unanswerable and irrelevant questions are evaluated separately.

They pass only when the generated answer explicitly states that the evidence is insufficient or the answer cannot be found.

## Model Configuration

- Model: `llama3.2:3b`
- Temperature: `0`
- Retrieval top-k: `5`

## Dataset

- Total cases: `32`
- Answerable cases: `20`
- Unsupported cases: `12`

## Numerical Results

- Answer correctness accuracy: `0.7500`
- Full citation accuracy: `0.8000`
- Mean citation coverage: `0.8893`
- Abstention accuracy: `1.0000`
- Overall case pass rate: `0.7500`
- Failure count: `8`

## Failure Examples

### eval-005

- Type: `direct`
- Question: What converts document chunks into vector embeddings?
- Answer correct: `False`
- Abstained: `None`
- Citation coverage: `1.0`

Model answer:

```text
ANSWER CANNOT BE FOUND IN THE PROVIDED DOCUMENT.
```

### eval-006

- Type: `direct`
- Question: What retrieves chunks relevant to the user question?
- Answer correct: `False`
- Abstained: `None`
- Citation coverage: `1.0`

Model answer:

```text
ANSWER CANNOT BE FOUND IN THE PROVIDED DOCUMENT.
```

### eval-013

- Type: `multi-part`
- Question: How does Docu AI retrieve information and generate an answer?
- Answer correct: `True`
- Abstained: `None`
- Citation coverage: `0.5`

Model answer:

```text
Based on the retrieved context, here is the answer:

Docu AI retrieves information and generates an answer through the following steps:

1. Similarity search retrieves document chunks relevant to the user's question (Result 3).
2. The local language model (Ollama) is used to process the document and application logic (Result 4).
3. The local language model (Ollama) is also used to generate answers (Result 4).
4. Streamlit provides the PDF upload and question-answer interface (Result 5).
5. Python is used for the document processing and application logic in Docu AI (Result 1).

Note: The sources conflict on the specific role of Ollama in generating answers, with Result 4 stating it generates answers and Result 2 stating it runs the local language model used for answer generation.
```

### eval-016

- Type: `multi-part`
- Question: What provides the user interface and what metadata supports traceability?
- Answer correct: `True`
- Abstained: `None`
- Citation coverage: `0.5`

Model answer:

```text
Based on the retrieved results, the user interface is provided by Python (Result 3), and the metadata that supports traceability is stored as metadata for source names and page numbers (Result 1 and Result 5).
```

### eval-017

- Type: `multi-part`
- Question: Which components handle embedding, storage, retrieval, and answer generation?
- Answer correct: `False`
- Abstained: `None`
- Citation coverage: `0.5`

Model answer:

```text
Based on the retrieved context, the components that handle embedding, storage, retrieval, and answer generation are:

- Embedding: Sentence Transformers (Result 4 and Result 5) and ChromaDB (Result 1 and Result 3)
- Storage: ChromaDB (Result 1 and Result 3)
- Retrieval: ChromaDB (Result 1 and Result 3) and Sentence Transformers (Result 4 and Result 5)
- Answer Generation: Ollama (Result 2)

Sources conflict on the storage component, with Result 1 and Result 3 stating ChromaDB, while Result 4 and Result 5 state Sentence Transformers.
```

### eval-018

- Type: `multi-part`
- Question: What happens from PDF upload through source traceability?
- Answer correct: `True`
- Abstained: `None`
- Citation coverage: `0.2857142857142857`

Model answer:

```text
Based on the retrieved context, here is the answer:

From PDF upload, the process involves the following steps:

1. The user uploads a PDF document through the Streamlit interface (Result 2).
2. PyPDF extracts text from each uploaded PDF page before further processing (Result 1).
3. The extracted text, along with source names and page numbers, is stored as metadata for traceability (Result 4).
4. Retrieved chunks retain source names and page numbers for traceability (Result 5).

This process allows for source traceability, enabling the tracking of the origin of the extracted text.
```

### eval-031

- Type: `conflicting`
- Question: According to the available sources, what is the Nova protocol timeout?
- Answer correct: `False`
- Abstained: `None`
- Citation coverage: `1.0`

Model answer:

```text
ANSWER CANNOT BE FOUND IN THE PROVIDED DOCUMENT.
```

### eval-032

- Type: `conflicting`
- Question: Do the Nova protocol sources agree on the timeout value?
- Answer correct: `False`
- Abstained: `None`
- Citation coverage: `1.0`

Model answer:

```text
ANSWER CANNOT BE FOUND IN THE PROVIDED DOCUMENT.
```

## Important Limitations

This evaluation does not use another language model as the sole judge of correctness.

Automated answer scoring uses lexical concept coverage against human-defined reference answers. This makes the rule reproducible and inspectable, but it is not a complete semantic understanding metric.

Equivalent wording may occasionally receive a lower score if it uses substantially different vocabulary from the reference answer.

Conversely, lexical overlap alone cannot prove that every generated statement is logically correct.

Citation evaluation verifies expected source, page, and controlled evidence markers, but does not replace human review of nuanced claims.

Abstention detection is based on explicit failure phrases and may not capture every possible wording of uncertainty.

For these reasons, automated metrics should be treated as reproducible engineering indicators, not as absolute truth.

## Reproducibility

Detailed per-case outputs are stored in `evaluation/answer-results.jsonl`.

Each record includes the model answer, expected citations, retrieval coverage, prompt, model name, temperature, and pass/fail fields.

## Conclusion

The evaluation combines human-authored reference data with transparent automated rules for answer correctness, citation support, and abstention.

Failures remain inspectable at the individual question level rather than being hidden behind aggregate metrics.