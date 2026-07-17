# ENGINEERING_DECISION_STANDARD.md

# Purpose

This standard defines the quality requirements for Decision Guide objects within the Engineering Knowledge Base (EKB).

An Decision Guide is not merely an opinion or recommendation.

It is a reusable engineering reasoning artifact that helps engineers make informed decisions across multiple projects and technologies.

This standard defines what makes an Decision Guide complete, useful, and trustworthy.

---

# Core Principle

An Decision Guide exists to improve engineering judgment.

It should teach engineers **how to reason**, not simply **what to choose**.

The objective is to increase decision quality rather than prescribe universal answers.

---

# Scope

This standard applies to all Knowledge Objects of type:

```yaml
type: decision_guide
```

It does not apply to:

* Concepts
* Patterns
* Quality Attributes
* Examples
* References

These have their own quality standards.

---

# Ontology

The canonical `type` for a DG-* object is `decision_guide`. The type names the
**artifact**, not its purpose:

* A **Decision Guide** is a reusable, verdict-free **decision-support artifact**.
* It is **not** an engineering decision. `engineering_decision` (a project
  decision or decision record) is a different object EKB does not currently
  store; that value is rejected for DG-* objects and reserved for future use.
* **EKB provides decision support.** **ECF produces recommendations.** **Humans
  approve or make project decisions.** The Decision Guide sits at the first of
  these stages: it improves engineering judgment; it does not render the verdict.

---

# Required Sections

Every Decision Guide shall contain the following sections.

---

## 1. Decision Statement

A single, clear engineering question.

Good examples:

* Should I introduce another subsystem?
* Should I split this requirement?
* Should this process become event-driven?

Poor examples:

* Architecture
* Microservices
* Event Sourcing

The title should always express a decision.

---

## 2. Context

Describe the engineering situation in which the decision occurs.

Context should answer:

* When does this decision arise?
* What is happening?
* Why is a decision required?

Avoid project-specific details unless used as examples.

---

## 3. Engineering Question

State the precise question that must be answered.

There should be exactly one primary engineering question.

---

## 4. Why This Decision Matters

Explain why this decision has engineering significance.

Examples:

* affects maintainability
* affects scalability
* difficult to reverse
* influences architecture
* introduces long-term cost

---

## 5. Engineering Forces

Describe the competing forces influencing the decision.

Examples include:

* complexity
* coupling
* cohesion
* performance
* security
* usability
* delivery speed
* maintainability

Forces should explain *why* the decision is difficult.

---

## 6. Alternatives

List realistic alternatives.

Each alternative should include:

* description
* appropriate context
* benefits
* drawbacks
* risks

Alternatives should be presented objectively.

---

## 7. Decision Heuristics

Provide practical guidance that helps engineers evaluate the alternatives.

Heuristics are:

* context-dependent
* experience-driven
* evidence-based

Heuristics are not absolute rules.

---

## 8. Common Mistakes

Describe mistakes frequently made when making this decision.

Explain:

* why the mistake occurs
* why it is problematic
* how to recognize it

---

## 9. Engineering Recommendation

Summarize the recommended reasoning.

This section should explain:

* when a particular alternative is usually appropriate
* when it should be avoided
* why

Avoid universal prescriptions.

---

## 10. Trade-offs

Describe the engineering compromises.

Good decisions acknowledge trade-offs.

Poor decisions pretend trade-offs do not exist.

---

## 11. Related Knowledge

Reference supporting Knowledge Objects.

These may include:

* Concepts
* Patterns
* Quality Attributes
* Examples
* References
* Other Decisions

Relationships should use stable IDs.

---

## 12. Confidence Guidance

Describe situations where confidence is:

* High
* Medium
* Low

Confidence should be based on available evidence and engineering understanding.

---

# Quality Criteria

A high-quality Decision Guide should be:

* understandable
* technology-neutral where practical
* reusable
* evidence-based
* trade-off aware
* context-sensitive
* internally consistent
* well referenced

---

# Validation Checklist

Before approval, verify:

* [ ] Decision Statement is clear.
* [ ] Context is complete.
* [ ] Engineering Question is explicit.
* [ ] Forces are identified.
* [ ] Multiple alternatives are considered.
* [ ] Trade-offs are discussed.
* [ ] Recommendation explains reasoning.
* [ ] Common mistakes are documented.
* [ ] Related Knowledge Objects are referenced.
* [ ] Stable IDs are used.
* [ ] Metadata complies with the Knowledge Object Standard.

---

# Review Questions

Reviewers should ask:

* Does this improve engineering judgment?
* Does it explain *why* rather than simply *what*?
* Are important alternatives missing?
* Are trade-offs represented fairly?
* Could this guide an engineer facing the decision for the first time?
* Would another experienced engineer understand and largely agree with the reasoning?

---

# Success Criteria

An Decision Guide is successful when:

* engineers can explain the reasoning behind the recommendation
* different engineers reach similar conclusions when given similar contexts
* AI systems produce consistent reasoning from the same inputs
* the decision remains useful across multiple projects

---

# Guiding Principle

The purpose of an Decision Guide is not to eliminate judgment.

The purpose is to improve the quality, consistency, and explainability of engineering judgment.
