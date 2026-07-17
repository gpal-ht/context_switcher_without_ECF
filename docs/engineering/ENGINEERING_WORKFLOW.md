# Engineering Workflow

## Purpose

This document defines how work moves from idea to implementation in the Context Switcher project.

The workflow exists to protect decision quality, code quality, user trust, and long-term maintainability.

Implementation is allowed only after the relevant design, review, and approval gates are complete.

---

# Core Principle

Confidence increases before implementation increases.

The project should not write code merely because code can be written.

A feature is ready for implementation only when the team understands:

* what problem it solves
* how it fits the product
* how it affects architecture
* how it affects knowledge
* how it affects runtime behavior
* how it will be tested
* what risks remain

---

# Standard Feature Lifecycle

Every significant feature follows this lifecycle:

1. Idea
2. Product Brief
3. Requirements
4. UX Flow
5. Architecture Impact
6. Knowledge Impact
7. Runtime Impact
8. AI Impact, if applicable
9. Security & Privacy Review
10. Accessibility Review
11. Test Strategy
12. Delivery Plan
13. Human Approval
14. Implementation
15. Self Review
16. Specialist Review
17. Merge Readiness

No implementation may begin before Human Approval.

---

# Gate 1 — Product Review

Answers:

* Does this support the product mission?
* Is this solving the right problem?
* Is it in scope for the current phase?
* Does it reduce cognitive load?
* Does it preserve user agency?

Primary owner:

* Product Architect

Output:

* Product Review

---

# Gate 2 — Architecture Review

Answers:

* Which subsystem owns this?
* Does it respect subsystem boundaries?
* Does it require a new ADR?
* Does it introduce a new dependency?
* Does it create architectural drift?

Primary owner:

* System Architect

Output:

* Architecture Review

---

# Gate 3 — Knowledge Review

Answers:

* Does this create or modify Knowledge Items?
* Does it affect Context Snapshots?
* Does it preserve provenance?
* Does it affect knowledge history?
* Does it introduce a new domain concept?

Primary owner:

* Knowledge Architect

Output:

* Knowledge Impact Assessment

---

# Gate 4 — Runtime Review

Answers:

* Does this affect active work sessions?
* Does this require recoverable runtime state?
* Does this need checkpoints?
* What happens if the app crashes?
* What events or commands are involved?

Primary owner:

* Runtime Architect

Output:

* Runtime Impact Assessment

---

# Gate 5 — AI Review

Required when a feature involves:

* AI summaries
* AI recommendations
* imported ChatGPT context
* repository-aware evaluation
* prompts
* external AI providers
* semantic search

Answers:

* What data is sent to AI?
* Is user approval required?
* Is the AI provider abstracted?
* Can the recommendation be explained?
* What hallucination risks exist?

Primary owner:

* AI Architect

Output:

* AI Impact Assessment

---

# Gate 6 — Security & Privacy Review

Required when a feature involves:

* local storage
* external systems
* AI providers
* imported data
* Git repositories
* user files
* secrets
* authentication

Answers:

* What sensitive data is involved?
* Is data stored securely?
* Is any data sent externally?
* Is user consent explicit?
* Are secrets protected?

Primary owner:

* Security Architect

Output:

* Security Assessment

---

# Gate 7 — Accessibility Review

Required for all user-facing features.

Answers:

* Is the feature keyboard accessible?
* Is focus order clear?
* Are labels and names available to assistive technologies?
* Is contrast sufficient?
* Is motion respectful and reducible?
* Is interruptive UI safe and understandable?

Primary owner:

* Accessibility Architect

Output:

* Accessibility Assessment

---

# Gate 8 — Test Strategy

Answers:

* What can be unit tested?
* What requires integration testing?
* What requires manual QA?
* What edge cases matter?
* What regression risks exist?

Primary owner:

* Test Architect

Output:

* Test Strategy

---

# Gate 9 — Delivery Plan

Answers:

* What is the smallest safe implementation slice?
* Which files or modules are likely to change?
* What order should work happen in?
* What checks must pass?
* What rollback or recovery strategy is needed?

Primary owner:

* Delivery Architect

Output:

* Delivery Plan

---

# Gate 10 — Human Approval

Implementation may begin only when the Project Owner explicitly says:

* "Approved to implement."
* "You may write the code."
* "Proceed with implementation."

Other phrases do not count as implementation approval.

---

# Implementation Rules

When implementation is approved:

* Work in small increments.
* Do not perform unrelated rewrites.
* Preserve architectural boundaries.
* Update tests and documentation as needed.
* Run or document required verification.
* Stop if the implementation reveals a design issue.

---

# Post-Implementation Review

Before merge, the change must include:

* Summary of what changed
* Verification performed
* Tests added or updated
* Manual QA steps
* Accessibility check
* Security/privacy check
* Known limitations
* Follow-up work

---

# Complexity Gate

Before introducing a new feature, document:

1. Which subsystem owns it.
2. Which domain concepts it affects.
3. Whether it introduces a new concept.
4. Whether it requires an ADR.
5. Whether it changes the product vision.

If these answers are unclear, implementation is not ready.

---

# Documentation Rule

No new document should be created unless it answers a question that cannot reasonably be answered by an existing document.

When a new document is created, update `docs/README.md`.

---

# Definition of Ready

A feature is ready for implementation only when:

* product value is clear
* architecture impact is understood
* knowledge impact is understood
* runtime behavior is understood
* risks are documented
* test strategy exists
* human approval has been given

---

# Definition of Done

A feature is complete only when:

* the approved plan was followed
* the implementation builds
* relevant tests pass
* manual QA is documented
* accessibility has been reviewed
* security/privacy has been reviewed
* documentation has been updated
* the change is small enough to review
