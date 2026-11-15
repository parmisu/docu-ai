# Vector Store Correctness Report

## Purpose

This report verifies that Docu AI stores vector records correctly and preserves the expected relationship between input chunks and stored records.

The test focuses on:

- input chunk count
- stored record count
- generated record IDs
- metadata preservation
- content preservation
- storage error visibility
- test isolation between vector-store instances

## Storage Policy

The expected storage policy is:

```text
one input chunk = one stored vector record
```

Each stored record must preserve:

- chunk text
- source document metadata
- page metadata

Each inserted record must also receive a non-empty unique ID.

Storage failures must not be silently ignored.

## Test Fixture

Controlled cases are stored in:

`tests/fixtures/vector_store_cases.json`

The fixture contains four controlled document chunks.

Each chunk includes:

- unique text marker
- source document name
- page number

Expected input record count:

```text
4
```

## Test File

Automated tests are implemented in:

`tests/test_vector_store.py`

The test suite verifies that:

- the fixture produces the expected number of input chunks
- one ID is returned for each stored chunk
- generated IDs are non-empty
- generated IDs are unique
- the number of stored records matches the number of input chunks
- stored text matches the original text
- source metadata is preserved
- page metadata is preserved
- storage exceptions are not silently ignored

## Record Count Verification

Four controlled chunks are inserted into Chroma.

After insertion, the test inspects:

```text
ids
documents
metadatas
```

Each collection must contain the same number of records as the input chunk list.

Expected:

```text
input chunks = 4
stored IDs = 4
stored documents = 4
stored metadata records = 4
```

## Record Identity

The IDs returned by Chroma are checked to ensure that:

- every inserted chunk receives an ID
- no ID is empty
- no two inserted records share the same ID

This confirms that each stored chunk has a distinct record identity.

## Metadata Preservation

For every stored record, the tests compare its metadata with the original input chunk.

The following values must remain unchanged:

```text
source
page
```

Stored document text is also matched against the original input content.

## Storage Failure Behavior

A simulated storage failure is introduced by replacing the vector-store insertion method with a function that raises:

```text
RuntimeError
```

The test confirms that this exception propagates instead of being silently ignored.

This ensures that a failed write cannot incorrectly appear as a successful storage operation.

## Initial Test-Isolation Failure

The first test execution produced:

```text
5 passed
1 failed
```

The failing assertion showed:

```text
8 stored records != 4 expected records
```

The cause was not a vector storage failure.

Multiple tests were using the same Chroma collection name:

```text
vector_store_test
```

This allowed records created by an earlier test to remain available to a later test.

The result was state leakage between tests.

## Test-Isolation Fix

The vector-store helper was updated so that each test receives a unique collection name using a UUID.

Example:

```python
collection_name=f"vector_store_test_{uuid4().hex}"
```

This ensures that every test begins with an isolated vector-store collection.

After this change, stored record counts matched the expected input counts.

## Final Test Execution

Command:

```bash
python -m pytest tests/test_vector_store.py -v
```

Observed result:

```text
6 passed
```

## Result

The controlled vector-store tests confirmed that:

- each input chunk produces one stored record
- stored record counts match input counts
- generated IDs are non-empty and unique
- original content is preserved
- source metadata is preserved
- page metadata is preserved
- simulated storage failures are visible
- vector-store test state is isolated between tests

## Conclusion

T18 confirms that the controlled Docu AI vector-store workflow behaves according to the expected storage policy.

The tests also exposed and corrected a test-isolation issue caused by reusing the same Chroma collection name across tests.

With isolated collections, record count, identity, metadata, and failure behavior are all explicitly verified.