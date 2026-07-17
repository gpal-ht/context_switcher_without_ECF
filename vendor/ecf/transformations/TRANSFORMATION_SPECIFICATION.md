# TRANSFORMATION_SPECIFICATION.md

# Purpose

Defines the standard contract that every Knowledge Transformation in ECF must follow.

Transformations are reusable engineering capabilities.

They consume engineering knowledge, apply engineering standards, and produce new engineering knowledge.

---

# Transformation Identity

* Transformation ID
* Name
* Version
* Status

---

# Purpose

Why does this transformation exist?

What engineering problem does it solve?

---

# Inputs

Canonical artifacts required.

Examples:

* Product Requirements
* Existing ADRs
* System Design

---

# Entry Criteria

Conditions that must be true before execution.

Examples:

* Required artifacts exist.
* Required standards identified.
* Required approvals complete.

---

# Standards Applied

List every engineering standard governing this transformation.

Examples:

* Product Requirements Standard
* System Design Standard
* UML Standard

---

# Transformation Rules

Describe how inputs become outputs.

This section defines the engineering reasoning process.

---

# Outputs

Canonical artifacts produced or updated.

Each output should reference its artifact specification.

---

# Quality Criteria

How do we know the transformation was successful?

Examples:

* Complete
* Traceable
* Internally consistent
* Review-ready

---

# Required Review Pack

Which Review Pack validates this transformation?

---

# Exit Criteria

Conditions required before downstream transformations may begin.

---

# Metrics

Examples:

* Transformation duration
* Review iterations
* Defects found
* Rework required

These metrics allow ECF to improve transformation quality over time.

---

# Lessons Learned

Optional observations that may improve future executions of the transformation.
