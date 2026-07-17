# PRODUCT_PRINCIPLES.md

# Product Principles

These principles guide every product decision.

When evaluating a new feature, architectural change, or AI capability, the first question is:

> Does this strengthen the mission of helping users preserve, transfer, and improve work context?

If the answer is unclear, the feature should not proceed until the value is understood.

---

# 1. User Agency Over Automation

The user is always in control.

The application may:

* recommend
* remind
* summarize
* suggest

The application must not:

* make irreversible decisions
* hide important information
* remove meaningful user choice

AI assists.

Humans decide.

---

# 2. Reduce Cognitive Load

Every feature should reduce mental effort.

If a feature requires more attention than it saves, it should be redesigned or removed.

The application should help users answer questions like:

* What was I doing?
* Why was I doing it?
* What should I do next?

without unnecessary friction.

---

# 3. Preserve Context, Not Just Data

Raw information has limited value.

The product should preserve:

* decisions
* reasoning
* intent
* assumptions
* blockers
* progress
* next actions

Context is more valuable than isolated notes.

---

# 4. Interrupt With Purpose

Interruptions should be intentional and beneficial.

Every interruption must have a clear objective.

Examples include:

* preventing an unplanned overrun
* encouraging reflection
* prompting a context handoff

Interruptions should never feel punitive or arbitrary.

---

# 5. Explain AI Recommendations

AI recommendations should be transparent.

Whenever practical, the application should help the user understand:

* what information was considered
* why the recommendation was made
* what assumptions were used
* what alternatives exist

Trust is built through explainability.

---

# 6. Local First

User data should remain on the user's device whenever practical.

Cloud services and external AI providers should be optional, transparent, and explicitly enabled.

Privacy is a product feature.

---

# 7. Build Long-Term Trust

Trust is difficult to earn and easy to lose.

The application should be:

* predictable
* respectful
* transparent
* recoverable

The user should always understand what the application is doing and why.

---

# 8. Small Features, Strong Foundations

Prefer improving existing workflows over adding new ones.

New capabilities should strengthen the product rather than expand it unnecessarily.

Every feature increases long-term maintenance cost.

That cost should be justified.

---

# 9. Design Before Implementation

Every significant feature should begin with:

* problem statement
* user value
* success criteria
* design review
* architecture review

Implementation is the final step.

---

# 10. Quality Is a Product Feature

Quality includes:

* usability
* accessibility
* reliability
* performance
* maintainability
* security
* privacy
* consistency

A feature that works but is difficult to understand or maintain is not considered complete.

---

# Feature Evaluation Checklist

Before accepting a new feature, ask:

1. Does it support the product mission?
2. Does it reduce cognitive load?
3. Does it preserve user agency?
4. Does it improve context rather than simply store data?
5. Is it understandable to users?
6. Can it be implemented without unnecessary complexity?
7. Does it respect privacy?
8. Can it be tested effectively?
9. Will it still make sense one year from now?
10. Is it worth the maintenance cost?

If several answers are "no" or "unclear," the feature should be redesigned or postponed.

---

# Decision Philosophy

When two solutions are technically equivalent, prefer the one that is:

1. Simpler.
2. Easier to understand.
3. Easier to maintain.
4. Easier to test.
5. More respectful of the user's attention and control.

Good engineering supports good products, and good products respect the people who use them.

The application owns the knowledge. AI interprets the knowledge. The user owns the decisions.

Measure learning and progress, not just completion.
