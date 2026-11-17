# Testing Guide

## Overview

Docu AI uses pytest for automated testing.

The test suite is divided into two categories:

- independent tests
- Ollama integration tests

Independent tests can run without a live Ollama service.

Integration tests require a running local Ollama service and the configured model.

## Environment

Tests should be executed from the project virtual environment.

Activate the environment:

```bash
source .venv/bin/activate
```

Verify Python:

```bash
python --version
```

The project currently targets Python 3.11.

Install project dependencies if required:

```bash
python -m pip install -r requirements.txt
```

Verify dependency consistency:

```bash
python -m pip check
```

## Test Configuration

Pytest configuration is stored in:

```text
pytest.ini
```

Tests are discovered under:

```text
tests/
```

using the naming convention:

```text
test_*.py
```

## Independent Test Run

The default test command is:

```bash
python -m pytest -v
```

Ollama-dependent integration tests are skipped automatically.

The skip reason identifies that they require a real local Ollama service.

This allows the main test suite to run reproducibly without depending on external local-service state.

## Ollama Integration Tests

The following tests require real Ollama execution:

```text
tests/test_answer_generation.py
tests/test_abstention.py
tests/test_conflicting_evidence.py
```

Before running them, verify Ollama:

```bash
ollama --version
```

Verify the configured model:

```bash
ollama list
```

Docu AI currently uses:

```text
llama3.2:3b
```

Run the full suite including Ollama tests with:

```bash
RUN_OLLAMA_TESTS=1 python -m pytest -v
```

Run only integration tests with:

```bash
RUN_OLLAMA_TESTS=1 python -m pytest -m integration -v
```

## Generated Test Evidence

The reproducible default run generates:

```text
artifacts/pytest-report.xml
artifacts/pytest-output.txt
```

Both artifacts must come from the same pytest execution.

The XML report contains machine-readable information about:

- executed tests
- passed tests
- failed tests
- errors
- skipped tests
- execution time

The text output preserves the terminal-visible pytest results.

## Generate the Test Reports

From the repository root:

```bash
set -o pipefail
python -m pytest -v \
  --junitxml=artifacts/pytest-report.xml \
  2>&1 | tee artifacts/pytest-output.txt
```

This performs one real pytest execution while producing both report formats.

## Failed Tests

Failed tests remain visible in:

```text
artifacts/pytest-output.txt
```

and:

```text
artifacts/pytest-report.xml
```

Failures must not be manually removed from the generated reports.

## Skipped Tests

Tests that require a real Ollama service are intentionally skipped during the default reproducible run.

They remain visible as skipped tests with an explicit reason.

They can be executed separately using:

```bash
RUN_OLLAMA_TESTS=1 python -m pytest -m integration -v
```

## Why Integration Tests Are Separated

A test that depends on a running local Ollama service may fail because of:

- Ollama not running
- configured model missing
- local service timeout
- local resource limitations
- model runtime failure

These conditions are different from deterministic application logic failures.

Separating integration tests prevents service availability from making the independent test suite unreliable.

## Reporting Policy

Generated reports represent the actual test execution.

The project does not manually convert:

```text
failed → passed
```

or:

```text
skipped → passed
```

in test artifacts.

Unexpected failures should remain visible and be investigated separately.

## Recommended Commands

Default reproducible test suite:

```bash
python -m pytest -v
```

Only independent tests:

```bash
python -m pytest -m "not integration" -v
```

Only Ollama integration tests:

```bash
RUN_OLLAMA_TESTS=1 python -m pytest -m integration -v
```

Full suite including Ollama:

```bash
RUN_OLLAMA_TESTS=1 python -m pytest -v
```