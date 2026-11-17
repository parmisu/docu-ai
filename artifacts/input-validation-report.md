# Input Validation Report

## Purpose

This report documents Docu AI's validation behavior for user questions before retrieval or model execution.

The goal is to reject invalid input early, avoid unnecessary Ollama calls, and provide clear feedback to the user.

## Current Validation Policy

Docu AI currently accepts questions that:

- contain non-whitespace content
- are written within the current English-language project scope
- are no longer than 500 characters

Invalid inputs are rejected before model invocation.

## Tested Input Cases

The controlled validation fixture is stored in:

`tests/fixtures/input-validation-cases.json`

The test coverage includes:

- empty input
- whitespace-only input
- normal English questions
- single-character boundary input
- exactly 500 characters
- input longer than 500 characters
- non-English-like or unsupported input
- validation before model execution

## Empty and Whitespace Input

Empty input and whitespace-only input are classified as:

```text
empty_input