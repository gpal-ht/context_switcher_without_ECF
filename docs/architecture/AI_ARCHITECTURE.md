# AI Architecture

## Purpose

This document defines how AI fits into Context Switcher.

AI should improve understanding, planning, reflection, and decision support without becoming the source of truth.

## Core Principle

The application owns the knowledge.

AI interprets the knowledge.

The user owns the decisions.

## AI Role

AI may help with:

- summarizing work sessions
- reconstructing project context
- identifying blockers
- suggesting next actions
- reviewing productivity patterns
- extracting decisions from imported context
- comparing possible priorities
- improving wrap-up quality

AI must not:

- silently change user data
- make irreversible decisions
- hide reasoning
- become required for basic app use
- replace the user's judgment

## AI Boundary

AI functionality must be isolated behind clear interfaces.

The rest of the application should not depend directly on:

- ChatGPT
- Claude
- any specific model provider
- any specific prompt format

## AI Provider Model

Potential providers:

- ChatGPT / OpenAI
- Claude / Anthropic
- local models
- future providers

Provider-specific code belongs behind an AI provider adapter.

## External Context Import

Imported context may come from:

- ChatGPT export
- manually imported files
- project notes
- future integrations

Imported context should move through this flow:

```text
Raw Import
    ↓
Parsing
    ↓
Classification
    ↓
Summarization
    ↓
User Review
    ↓
Accepted Knowledge

## Repository-Aware Work Evaluation

When a work session is associated with a GitHub repository, AI may help evaluate work against the user's stated session expectations.

The goal is not to replace human judgment, but to provide structured feedback.

### Inputs

Potential inputs include:

- session objective
- planned scope
- acceptance criteria
- changed files
- commits
- pull request description
- test results
- lint/type-check results
- code review notes
- performance measurements where available

### Evaluation Areas

AI may assess:

- estimated completion percentage
- alignment with the stated goal
- code quality
- maintainability
- test coverage
- accessibility impact
- performance risk
- security/privacy risk
- unresolved work
- recommended next steps

### Output

A repository-aware work evaluation should produce:

- summary of work completed
- comparison against session expectations
- evidence used
- completion estimate
- quality assessment
- risks
- open questions
- recommended next action

### Constraints

AI must not treat repository analysis as absolute truth.

The evaluation must clearly distinguish between:

- evidence from the repository
- AI inference
- uncertainty
- missing information

The user remains responsible for final judgment.

## Open Questions

- Should GitHub integration be read-only at first?
- Should evaluation happen per session, commit, branch, or pull request?
- How should completion percentage be calculated?
- What evidence is required before AI can judge quality?
- Should the app integrate with GitHub directly or read from a local repository first?

