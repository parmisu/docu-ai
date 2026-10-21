# Initial Test Inventory

## Purpose

This document records the testing state of Docu AI before new automated tests are introduced.

The purpose of this inventory is to distinguish the existing project state from failures or results produced by tests that will be added later.

---

## Test Runner Availability

The project environment was checked using:

```bash
python -m pytest --version
```

Observed result:

```text
/Users/parmisu/docu-ai/.venv/bin/python: No module named pytest
```

Pytest was therefore not available in the verified project environment at the time of this inventory.

This is an environment/tooling condition, not a failing test result.