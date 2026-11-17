# Conflicting Evidence Evaluation

## Purpose

This evaluation tests whether Docu AI handles contradictory source evidence without presenting one unsupported claim as definitive truth.

## Retrieved Evidence

### Rank 1

- Source: `source_a.txt`
- Page: `1`
- Score: `0.739515`

SOURCE_A_MARKER
According to Source A, the Nova protocol timeout is 30 seconds.

### Rank 2

- Source: `source_b.txt`
- Page: `1`
- Score: `0.709533`

SOURCE_B_MARKER
According to Source B, the Nova protocol timeout is 60 seconds.

## Model Answer

There is a conflict between the two sources.

According to Source A, the Nova protocol timeout is 30 seconds. (Source A)

According to Source B, the Nova protocol timeout is 60 seconds. (Source B)

There is no evidence provided in the sources to resolve the conflict, so we cannot determine a definitive answer.

## Evaluation

- Conflict acknowledged: `True`
- Both conflicting claims preserved: `True`
- Both sources identified: `True`

## Expected Policy

When retrieved sources disagree, the system must expose the disagreement or state that the evidence is insufficient to resolve it.

It must not select one conflicting claim as definitive truth without supporting evidence that resolves the conflict.