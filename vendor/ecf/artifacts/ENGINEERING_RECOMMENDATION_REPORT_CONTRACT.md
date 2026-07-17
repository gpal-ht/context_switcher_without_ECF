# Engineering Recommendation Report Contract

## Required Inputs

- Engineering Context
- Engineering Knowledge Package
- Engineering Question

## Required Sections

1. Work Request
2. Current Engineering Context
3. Retrieved Engineering Knowledge
4. Reasoning Trace
5. Engineering Forces
6. Alternatives
7. Trade-offs
8. Recommendation
9. Confidence
10. Missing Information
11. Suggested Next Transformation

## Rule

The report recommends.

The human decides.

# Confidence Assessment

Every Engineering Recommendation Report shall include a multidimensional confidence assessment.

Confidence must always answer:

> **Confidence in what?**

A single confidence score is not sufficient.

---

## Recommendation Confidence

Question:

How confident are we that this is currently the best engineering recommendation?

Provide:

* High
* Medium
* Low
* Unknown

Include justification.

---

## Evidence Confidence

Question:

How complete and trustworthy is the engineering evidence?

Consider:

* engineering artifacts
* measurements
* ADRs
* architecture
* validated assumptions

Include justification.

---

## Context Confidence

Question:

How well do we understand the engineering context?

Consider:

* project maturity
* known constraints
* architectural understanding
* stakeholder understanding

Include justification.

---

## Reversibility Confidence

Question:

If this recommendation proves incorrect, how easily can it be reversed?

Consider:

* implementation cost
* architectural impact
* migration effort
* operational risk

Include justification.

---

## Implementation Confidence

Question:

Assuming approval is granted, how confident are we that implementation will succeed?

Consider:

* technical complexity
* engineering knowledge
* available skills
* dependencies
* implementation risk

Include justification.

---

## Overall Confidence

Provide a narrative summary.

Do not average the previous confidence dimensions.

Explain how the individual confidence dimensions influence the engineering recommendation.

Overall Confidence should describe engineering uncertainty rather than compress it into a single score.
