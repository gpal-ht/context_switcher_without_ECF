# ENGINEERING_ORGANIZATION.md

# Purpose

This document defines the engineering organization responsible for designing, reviewing, implementing, and maintaining Context Switcher.

The organization exists independently of any AI tool.

Claude Code, other AI assistants, and human contributors should adopt these roles rather than replace them.

The objective is to ensure every engineering decision receives appropriate review before implementation.

---

# Engineering Philosophy

Engineering exists to increase confidence.

The objective is **not** to generate code quickly.

The objective is to make well-reasoned decisions that lead to maintainable, trustworthy software.

Implementation is the final engineering activity—not the first.

---

# Organizational Structure

The engineering organization consists of three groups.

## Tier 1 — Architecture Team

Responsible for product and technical design.

These roles shape the system.

### Product Architect

**Mission**

Protect the product vision.

**Owns**

* Product value
* Feature scope
* User workflows
* MVP boundaries

**Authority**

May reject features that do not support the product mission.

**Primary Artifact**

Product Review

---

### System Architect

**Mission**

Protect architectural integrity.

**Owns**

* subsystem boundaries
* architecture consistency
* ADR compliance
* dependency rules

**Authority**

May require an ADR before implementation.

**Primary Artifact**

Architecture Review

---

### Knowledge Architect

**Mission**

Protect the knowledge model.

**Owns**

* Knowledge Items
* Context Snapshots
* Knowledge evolution
* provenance
* knowledge relationships

**Authority**

May reject designs that compromise knowledge integrity.

**Primary Artifact**

Knowledge Impact Assessment

---

### Runtime Architect

**Mission**

Protect runtime correctness.

**Owns**

* runtime state
* work sessions
* event flow
* checkpointing
* recovery

**Authority**

May reject designs that compromise recovery or runtime consistency.

**Primary Artifact**

Runtime Impact Assessment

---

### Delivery Architect

**Mission**

Transform approved designs into implementation plans.

**Owns**

* implementation sequencing
* work breakdown
* dependencies
* rollout strategy

**Authority**

May delay implementation if the feature cannot be delivered safely in incremental steps.

**Primary Artifact**

Delivery Plan

---

# Tier 2 — Quality Team

Responsible for protecting quality attributes.

These specialists may block implementation when quality standards are not met.

### Security Architect

Protects:

* privacy
* secrets
* secure storage
* AI data boundaries
* external integrations

May block implementation.

Produces:

Security Assessment.

---

### Accessibility Architect

Protects:

* keyboard navigation
* screen reader support
* contrast
* focus management
* motion preferences
* WinUI accessibility

May block implementation.

Produces:

Accessibility Assessment.

---

### Test Architect

Protects:

* testability
* regression prevention
* verification strategy
* edge cases
* automation

May block implementation if adequate verification is missing.

Produces:

Test Strategy.

---

### Performance Architect

Protects:

* startup time
* responsiveness
* memory usage
* background processing
* scalability

Produces:

Performance Assessment.

---

### AI Architect

Protects:

* AI boundaries
* explainability
* prompt quality
* provider independence
* hallucination risks
* recommendation quality

Produces:

AI Impact Assessment.

---

# Tier 3 — Governance Team

Responsible for protecting the repository itself.

These roles review engineering discipline rather than product functionality.

### Repository Guardian

Protects:

* repository organization
* document consistency
* architectural drift
* duplicate concepts

Produces:

Repository Health Report.

---

### ADR Guardian

Protects:

* architectural decision records
* decision traceability
* ADR completeness
* review triggers

Produces:

ADR Compliance Report.

---

### Documentation Guardian

Protects:

* documentation quality
* consistency
* discoverability
* cross references

Produces:

Documentation Review.

---

# Engineering Workflow

Every significant feature follows this sequence.

1. Product Review
2. Architecture Review
3. Knowledge Review
4. Runtime Review
5. AI Review (if applicable)
6. Security Review (if applicable)
7. Accessibility Review
8. Performance Review
9. Test Strategy
10. Delivery Plan
11. Human Approval
12. Implementation
13. Post-Implementation Review

Reviews may be skipped only when the feature clearly does not affect the corresponding area.

---

# Blocking Authority

The following roles may prevent implementation from proceeding:

* Product Architect
* System Architect
* Knowledge Architect
* Runtime Architect
* Security Architect
* Accessibility Architect
* Test Architect

Blocking decisions must include:

* rationale
* affected principles
* recommended resolution

---

# Human Authority

The Project Owner is the final decision-maker.

AI reviewers advise.

Architects review.

The Project Owner approves.

No implementation begins without explicit approval.

---

# Guiding Principle

Engineering quality comes from disciplined decisions, clear responsibilities, and continuous review—not from trusting a single AI response.
