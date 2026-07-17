# EXP-0002 Finding

## Result

Partially Supported

## Summary

All tested models converged on the same recommendation: defer introducing Repository Integration as a first-class subsystem.

However, confidence calibration diverged.

ChatGPT and Claude assigned Medium confidence because the project context contains unresolved architectural questions and no implementation evidence.

Gemini assigned High confidence because the same unresolved questions strongly support deferral under the Decision Guide.

## Interpretation

The engineering recommendation is stable.

The confidence model is not yet stable.

## Required Improvement

Define a Confidence Calibration Standard.

The standard should clarify:

- confidence in recommendation direction
- confidence in evidence completeness
- confidence in timing
- confidence in reversibility
- confidence in long-term correctness

## Decision

Do not treat EXP-0002 as fully supported until confidence calibration is standardized and re-tested.