# PDF Performance Evaluation Report

## Purpose

This report records the current PDF-processing performance of Docu AI before further performance optimization.

The evaluation includes both:

1. a controlled synthetic 50-page PDF fixture
2. a larger real-world PDF processed through the Streamlit application

The results represent observed development-machine behavior and are not production performance guarantees.

## Predetermined Acceptance Threshold

Before running the controlled performance test, the following threshold was defined:

> A controlled 50-page text PDF should complete PDF parsing and text extraction in under 10 seconds on the verified development machine, without crashing or losing pages.

This threshold was defined before observing the measured extraction time.

## Controlled Test Fixture

File:

`tests/fixtures/pdf/large_sample.pdf`

Generation script:

`generate_large_pdf.py`

Properties:

- Pages: 50
- File size: 28,114 bytes
- Expected non-empty pages: 50
- Each page contains a unique traceable page marker

## Automated Test

Test file:

`tests/test_large_pdf.py`

The automated tests verify:

- expected page count
- successful extraction from every page
- preservation of unique page markers
- extraction time below the predetermined threshold

Command:

```bash
python -m pytest tests/test_large_pdf.py -v
```

Observed result:

```text
3 passed in 0.14s
```

The pytest duration represents the full test session and is not used as the precise extraction measurement.

## Controlled Extraction Measurement

A separate `time.perf_counter()` measurement was used for PDF parsing and text extraction.

Observed results:

```text
Pages: 50
File size bytes: 28114
Extraction seconds: 0.014055
Non-empty pages: 50
```

### Threshold Result

Predetermined threshold:

`< 10 seconds`

Observed extraction time:

`0.014055 seconds`

Result:

**PASS**

All 50 pages produced non-empty extracted text.

## Real-World Large PDF Observation

A larger real-world PDF was also manually tested through the Streamlit interface.

Observed document properties:

- File size: 31.3 MB
- Pages: 991
- Generated chunks: 1,639

Observed document preparation time:

- approximately 15 seconds

The application reached the `Document ready` state without crashing.

The interface remained usable after processing.

## Large-Document Question Test

Question:

```text
What is a foundation model?
```

Observed answer-generation time:

- approximately 5 seconds

The retrieval stage returned source pages including:

- Page 119
- Page 48
- Page 78
- Page 113

The generated answer was:

```text
I could not find the answer in the uploaded document.
```

This observation is recorded as retrieval/generation behavior rather than a performance failure.

Answer quality and retrieval relevance require separate evaluation and are outside the primary scope of this performance test.

## Resource Measurement Limitations

Exact process memory usage was not instrumented during this evaluation.

Therefore, this report does not claim a measured RAM peak or memory-consumption value.

Observed UI responsiveness and successful completion are recorded, but they are not substitutes for formal memory profiling.

A future performance evaluation could add:

- process-level peak memory measurement
- embedding-generation timing
- vector-store creation timing
- retrieval latency
- LLM generation latency
- repeated-run statistics
- performance across different file sizes

## Current Size Observations

The controlled 50-page document completed extraction comfortably below the predefined threshold.

A real-world 991-page, 31.3 MB PDF also completed application preparation successfully in approximately 15 seconds.

These observations establish a development baseline only.

They do not establish a maximum supported document size.

## Conclusion

Docu AI successfully processed both the controlled 50-page fixture and a substantially larger real-world document without crashing.

The controlled extraction benchmark passed the predetermined 10-second threshold.

The large real-world test demonstrated that the current application can process a 991-page, 31.3 MB document, although retrieval and answer quality remain separate concerns requiring dedicated evaluation.