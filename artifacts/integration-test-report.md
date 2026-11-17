# PDF-to-Answer Integration Test Report

## Purpose

This report verifies the complete Docu AI processing path from a known PDF fixture through extraction, chunking, vector storage, retrieval, answer generation, and citation validation.

## Controlled Input

The integration fixture is:

```text
tests/fixtures/pdf/document_a.pdf
```

The document contains the controlled fact:

```text
The Aurora research project uses a cobalt-blue sensor network.
```

The evaluation question is:

```text
What sensor network does the Aurora research project use?
```

The expected answer concept is:

```text
cobalt-blue
```

The expected supporting evidence is:

```text
cobalt-blue sensor network
```

The expected citation is:

```text
source = document_a.pdf
page = 1
```

## Pipeline Under Test

The complete tested path is:

```text
PDF fixture
→ PyPDF extraction
→ LangChain Document creation
→ RecursiveCharacterTextSplitter
→ embeddings
→ Chroma vector store
→ top-k retrieval
→ context construction
→ answer generation
→ answer validation
→ citation validation
```

## Simulated Integration Test

The simulated integration path uses:

- the real PDF fixture
- real PDF extraction
- real chunking
- real Chroma storage
- real retrieval flow
- deterministic test embeddings
- a controlled answer model

This mode avoids dependence on Ollama and provides a reproducible integration test for the application pipeline.

The simulated test is:

```text
test_simulated_pdf_to_answer_pipeline
```

It verifies that:

- PDF text is extracted
- chunks are created
- vector records are stored
- relevant evidence is retrieved
- the generated answer contains the expected answer concept
- the citation points to the correct file and page
- the cited text actually contains the full supporting evidence

## Real Ollama Integration Test

The real-service test is:

```text
test_real_ollama_pdf_to_answer_pipeline
```

This path uses:

```text
sentence-transformers/all-MiniLM-L6-v2
llama3.2:3b
Ollama
```

The real Ollama integration test was executed separately from the simulated path.

Run it with:

```bash
RUN_OLLAMA_TESTS=1 python -m pytest tests/integration/test_pdf_to_answer.py -v
```

Observed result:

```text
2 passed
```

This confirms that both the simulated integration path and the real Ollama path completed successfully.

## Separation of Test Modes

The two execution modes are recorded separately in:

```text
evaluation/integration-results.jsonl
```

The recorded modes are:

```text
simulated
real_ollama
```

This prevents a deterministic simulated test from being presented as evidence of a real Ollama integration run.

## Answer Validation

The answer check is concept-based rather than exact-string based.

For this controlled question, the generated answer must contain:

```text
cobalt-blue
```

This allows concise equivalent answers such as:

```text
cobalt-blue
```

as well as:

```text
The Aurora research project uses a cobalt-blue sensor network.
```

The test does not require the model to reproduce the full reference sentence word-for-word.

## Citation Validation

Citation validation remains stricter than answer wording.

A citation passes only when all of the following match:

```text
source name
page number
supporting evidence text
```

For this test the retrieved source must be:

```text
document_a.pdf
```

the page must be:

```text
1
```

and the cited content must contain:

```text
cobalt-blue sensor network
```

The existence of a source name or page number alone is not sufficient.

## Acceptance Criteria

The integration path passes when:

- extraction succeeds
- at least one chunk is produced
- retrieval returns evidence
- the generated answer contains the expected answer concept
- the retrieved citation points to `document_a.pdf`
- the citation page is `1`
- the cited content contains the expected supporting fact
- the simulated and real Ollama executions are reported separately

## Results

Detailed machine-readable results are stored in:

```text
evaluation/integration-results.jsonl
```

Both integration modes passed:

```text
simulated → overall_pass = true
real_ollama → overall_pass = true
```

## Warning Observed During Simulated Retrieval

The deterministic test embedding produced a Chroma relevance-score warning because the artificial similarity value was outside the expected normalized 0–1 relevance range.

This warning did not cause the simulated integration test to fail.

The deterministic embedding exists only to make the simulated integration path reproducible and is not the embedding model used by the production application.

The real Ollama integration path uses:

```text
sentence-transformers/all-MiniLM-L6-v2
```

## Conclusion

T41 provides an end-to-end integration check for the known PDF-to-answer workflow.

The deterministic simulated path provides reproducible pipeline coverage, while the separately executed real Ollama path verifies the workflow against the actual local model service.

Both paths successfully verified extraction, retrieval, answer generation, and citation correctness for the controlled PDF fixture.