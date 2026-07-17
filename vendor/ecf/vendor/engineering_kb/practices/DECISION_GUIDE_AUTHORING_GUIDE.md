# ENGINEERING_DECISION_AUTHORING_GUIDE.md

# Purpose

This guide explains how to create high-quality Decision Guide objects for the Engineering Knowledge Base (EKB).

Unlike the Decision Guide Standard, which defines quality requirements, this guide explains the reasoning process used to create reusable engineering decisions.

The objective is not to document opinions.

The objective is to capture engineering reasoning that remains valuable across projects, technologies, and time.

---

# Philosophy

Engineers are paid to make decisions under uncertainty.

An Decision Guide should teach someone how experienced engineers approach that uncertainty.

Good Decision Guides improve judgment.

They do not replace judgment.

---

# The Authoring Process

Creating an Decision Guide follows a repeatable reasoning process.

---

# Step 1 — Identify the Decision

The title must be a decision.

Good:

* Should I introduce another subsystem?
* Should this process become event-driven?
* Should I split this requirement?

Poor:

* Architecture
* CQRS
* Layering

A reader should immediately understand the engineering choice being considered.

---

# Step 2 — Understand the Context

Ask:

* When does this decision occur?
* What usually triggers it?
* What engineering maturity is required before the decision exists?
* Is this an early-stage decision or a late-stage decision?

Describe the engineering situation, not a specific project.

---

# Step 3 — Identify the Competing Forces

Every meaningful engineering decision exists because multiple forces compete.

Examples:

* maintainability
* complexity
* coupling
* cohesion
* performance
* delivery speed
* security
* cost
* usability

Avoid writing recommendations before understanding the forces.

---

# Step 4 — Identify the Alternatives

List realistic alternatives.

Avoid:

* impossible options
* strawman alternatives
* biased descriptions

Each alternative should represent a reasonable engineering choice.

---

# Step 5 — Explain Trade-offs

Trade-offs are the heart of engineering.

For every alternative ask:

* What becomes easier?
* What becomes harder?
* Who benefits?
* Who pays the cost?
* What changes in the future?

Avoid presenting one alternative as universally correct.

---

# Step 6 — Derive Engineering Heuristics

Heuristics help engineers reason.

Good heuristic:

"If responsibilities change independently, consider separating them."

Poor heuristic:

"Always create another subsystem."

Heuristics should:

* be contextual
* explain reasoning
* acknowledge exceptions

---

# Step 7 — Identify Common Mistakes

Ask:

What mistakes do inexperienced engineers commonly make?

Examples:

* optimizing too early
* creating unnecessary abstractions
* confusing implementation with architecture
* designing for hypothetical future requirements

Explain why each mistake is attractive and why it causes problems.

---

# Step 8 — Connect Knowledge

Every Decision Guide should connect to the broader Engineering Knowledge Graph.

Reference:

* Concepts
* Patterns
* Quality Attributes
* Examples
* Related Decisions

Never duplicate knowledge already explained elsewhere.

---

# Step 9 — Evaluate Confidence

Ask:

How confident should an engineer be?

High confidence:

Strong evidence and broad applicability.

Medium confidence:

Context matters significantly.

Low confidence:

Limited evidence or rapidly changing practice.

Confidence should always be justified.

---

# Step 10 — Review the Decision

Before approval ask:

* Does the document teach reasoning rather than rules?
* Does it explain why?
* Are alternatives treated fairly?
* Are trade-offs explicit?
* Could another experienced engineer follow the reasoning?
* Does it improve engineering judgment?

---

# Writing Style

Decision Guides should be:

* objective
* evidence-based
* technology-neutral where practical
* reusable
* concise
* explainable

Avoid:

* dogma
* absolute language
* tool-specific bias
* unsupported opinions

---

# Common Anti-Patterns

Do not:

* prescribe universal solutions
* confuse preferences with principles
* ignore trade-offs
* optimize for one quality attribute while hiding the cost to others
* duplicate existing knowledge
* answer multiple unrelated engineering questions in one Decision

---

# Definition of Excellence

A high-quality Decision Guide should allow different experienced engineers to reach similar conclusions when presented with similar contexts.

The objective is not identical answers.

The objective is consistent engineering reasoning.

---

# Guiding Principle

An Decision Guide should never tell an engineer what to think.

It should teach the engineer how to think about the decision.
