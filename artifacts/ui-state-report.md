# UI and Application State Recovery Report

## Purpose

This report documents Docu AI's document-processing state behavior across successful uploads, processing failures, retries, and application reruns.

The goal is to ensure that the interface reflects the real document state and does not present stale or failed documents as successfully processed.

## State Model

Docu AI distinguishes between:

- active document
- pending document
- processing state
- ready state
- error state
- empty state

A document becomes active only after processing completes successfully.

## New Upload

When a new document begins processing:

```text
status = processing
pending document = new upload
active document = previous successful document, if any