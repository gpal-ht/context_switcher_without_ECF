# CONFIDENCE_MODEL.md

# Purpose

This document defines the Engineering Confidence Model used throughout the Engineering Control Framework (ECF).

Engineering recommendations should communicate not only **what** is recommended but also **where uncertainty exists**.

Confidence is multidimensional.

A single confidence score is insufficient for engineering decision making.

---

# Core Principle

Engineering confidence is confidence in a specific aspect of reasoning.

Every confidence statement must answer:

> **Confidence in what?**

---

# Confidence Dimensions

Every Engineering Recommendation Report should assess the following dimensions.

---

# 1. Recommendation Confidence

## Question

How confident are we that this is currently the best engineering recommendation?

This evaluates the recommendation itself.

It does not evaluate implementation risk.

---

# 2. Evidence Confidence

## Question

How complete and trustworthy is the available engineering evidence?

Evidence includes:

* engineering artifacts
* measurements
* architectural documentation
* requirements
* observed behavior
* validated assumptions

Missing evidence should reduce Evidence Confidence.

---

# 3. Context Confidence

## Question

How well do we understand the engineering context?

Examples:

* project maturity
* architectural understanding
* known constraints
* stakeholder needs
* current system state

Unknown context should reduce Context Confidence.

---

# 4. Reversibility Confidence

## Question

If this recommendation proves incorrect, how easily can it be reversed?

Examples:

High:

* documentation changes
* small refactoring
* isolated architecture

Low:

* public API changes
* database migrations
* irreversible production changes

Engineering often prefers reversible decisions when uncertainty is high.

---

# 5. Implementation Confidence

## Question

Assuming approval is granted, how confident are we that implementation will succeed?

Consider:

* technical complexity
* available knowledge
* implementation dependencies
* engineering risk

Implementation confidence is independent of recommendation confidence.

---

# Overall Confidence

Overall Confidence should never be computed as a simple average.

Instead, it should summarize the engineering situation.

Examples:

* Recommendation is strong but evidence is incomplete.
* Recommendation is tentative due to limited context.
* Recommendation is strong and implementation risk is low.

Overall Confidence should explain rather than compress.

---

# Confidence Levels

Recommended levels:

* High
* Medium
* Low
* Unknown

Confidence should always include justification.

---

# Confidence Evolution

Confidence is expected to change.

As engineering progresses:

* evidence increases
* context improves
* uncertainty decreases

Confidence should generally increase through engineering work rather than intuition.

---

# Relationship to EKB

Engineering Knowledge provides reasoning guidance.

Engineering Confidence communicates the reliability of the resulting recommendation within a specific project context.

---

# Guiding Principle

Confidence should communicate engineering uncertainty, not personal certainty.
