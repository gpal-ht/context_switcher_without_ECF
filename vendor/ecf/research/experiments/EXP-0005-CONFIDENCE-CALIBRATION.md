# EXP-0005: Confidence Calibration

## Purpose

Determine whether explicit engineering confidence dimensions improve consistency across different reasoning engines.

---

# Hypothesis

When confidence is decomposed into explicit engineering dimensions, different AI models will converge more closely than when asked for a single overall confidence rating.

---

# Engineering Question

Should Repository Integration become a first-class subsystem in Context Switcher?

---

# Inputs

Use exactly the same inputs as EXP-0002:

* Engineering Context
* Engineering Knowledge Package

No additional information may be introduced.

---

# Instructions

Generate an Engineering Recommendation Report.

Replace the single confidence section with the following assessment.

## Confidence Assessment

Provide:

### Recommendation Confidence

State:

* High
* Medium
* Low
* Unknown

Explain why.

---

### Evidence Confidence

State:

* High
* Medium
* Low
* Unknown

Explain why.

---

### Context Confidence

State:

* High
* Medium
* Low
* Unknown

Explain why.

---

### Reversibility Confidence

State:

* High
* Medium
* Low
* Unknown

Explain why.

---

### Implementation Confidence

State:

* High
* Medium
* Low
* Unknown

Explain why.

---

### Overall Confidence

Provide a narrative summary.

Do not average the previous ratings.

Explain how the dimensions combine to support the engineering recommendation.

---

# Success Criteria

The experiment is considered successful when:

* models produce similar confidence profiles
* differences are explainable
* reasoning becomes more transparent
* reviewers can identify exactly where uncertainty exists

---

# Failure Criteria

The experiment fails when:

* models still produce significantly different confidence profiles without clear justification
* confidence dimensions remain ambiguous
* Overall Confidence contradicts individual dimensions

---

# Expected Finding

Engineering confidence should become more consistent because uncertainty is expressed explicitly rather than compressed into a single value.

If successful, the Engineering Recommendation Report Contract should permanently adopt the multidimensional confidence model.
