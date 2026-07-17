# Context Switcher Engineering Constitution

## Prime Directive

This repository follows a **design-first, implementation-second** philosophy.

No implementation code may be written until the user explicitly approves the relevant design and implementation plan.

The objective is not just to build software, but to build software deliberately, with every important decision understood and documented.

---

# Long-Term Vision

This project aims to build an **AI-assisted personal work operating system** for Windows.

The application will help users:

* Preserve work context across interruptions.
* Transition intentionally between tasks and projects.
* Record work progress with minimal friction.
* Reduce cognitive load during context switching.
* Build a persistent knowledge base of projects and work history.
* Provide AI-assisted recommendations to improve productivity and decision-making.
* Continuously learn from the user's work patterns while maintaining user control and privacy.

The initial focus timer is only the first capability of this larger vision.

---

# Guiding Principles

1. **Design before implementation.**
2. **Small, reviewable changes over large rewrites.**
3. **Human decisions take precedence over AI decisions.**
4. **Documentation is part of the product.**
5. **Quality is engineered, not inspected in afterwards.**
6. **Every design decision should be explainable.**
7. **User trust, privacy, and control are fundamental.**

---

# Current Phase

The project is currently in the **Foundation Phase**.

Activities allowed:

* Product definition
* Engineering governance
* Architecture design
* UX design
* Research
* Decision records
* Prototypes (only with explicit approval)

Activities not allowed:

* Production implementation
* Large-scale code generation
* Premature optimization

---

# Human Approval Gate

Claude must **never** generate implementation code unless the user explicitly authorizes it.

Valid approvals include:

* "Approved to implement."
* "You may write the code."
* "Proceed with implementation."

Statements such as:

* "Looks good."
* "Continue."
* "Next."

are **not** implementation approval.

---

# Required Feature Workflow

Every feature follows the same engineering lifecycle:

1. Product Brief
2. Goals and Success Criteria
3. Functional Requirements
4. Non-functional Requirements
5. UX Flow
6. Architecture Design
7. Data Model
8. Risks and Trade-offs
9. Accessibility Review
10. Security & Privacy Review
11. Test Strategy
12. Implementation Plan
13. Human Approval
14. Implementation
15. Self Review
16. Specialist Review
17. Merge Readiness

No steps may be skipped without explicit approval.

---

# AI Collaboration Principles

AI is an engineering collaborator—not an autonomous developer.

AI should:

* Explain its reasoning.
* Present alternatives when appropriate.
* Identify assumptions.
* Highlight risks.
* Ask for clarification when requirements are ambiguous.
* Recommend rather than silently decide.

AI should never:

* Invent requirements.
* Make product decisions on behalf of the user.
* Perform large refactors without approval.
* Introduce unnecessary complexity.

---

# Architecture Principles

The system should remain modular and evolve through well-defined boundaries.

Key principles:

* Separation of concerns.
* MVVM for presentation logic.
* Business logic isolated from UI.
* AI functionality isolated behind clear interfaces.
* Data storage abstracted from application logic.
* Dependency inversion where appropriate.
* Prefer simple solutions over clever ones.

---

# Quality Standards

Every proposed implementation must consider:

* Correctness
* Readability
* Maintainability
* Testability
* Performance
* Accessibility
* Security
* Privacy
* Observability (where appropriate)

---

# Safety Principles

The application must never behave like malware.

It must not:

* Block Windows security shortcuts.
* Prevent the user from exiting.
* Hide itself from normal Windows controls.
* Install persistence or auto-start without explicit approval.
* Collect or transmit user data without explicit design approval.

Interruptive experiences must always provide a documented and intentional escape path.

---

# Documentation Standards

Important decisions belong in the repository.

Documentation includes:

* Product vision
* Architecture
* ADRs (Architecture Decision Records)
* Feature specifications
* Review notes
* Engineering standards

If an important decision exists only in a chat conversation, it should be documented before implementation begins.

---

# Definition of Done

A feature is complete only when:

* The approved design has been implemented.
* The implementation satisfies the agreed requirements.
* Quality gates have been completed.
* Tests have been added or updated where appropriate.
* Manual QA steps are documented.
* Accessibility has been reviewed.
* Security and privacy impacts have been reviewed.
* Documentation has been updated.
* The change is ready for independent review.

---

# Continuous Improvement

This constitution is a living document.

Changes require discussion, documented reasoning, and explicit approval before adoption.
