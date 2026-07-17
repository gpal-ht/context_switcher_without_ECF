# ENGINEERING_INTENT_MODEL.md

# Purpose

This document defines the Engineering Intent Model used throughout the Engineering Knowledge Base (EKB).

Engineering Intent describes **why** engineering work is being performed.

It is the primary classification used to select engineering knowledge, reasoning strategies, engineering tasks, transformations, reviews, and workflows.

Engineering Intent is independent of any project, framework, or AI system.

---

# Philosophy

Engineering begins with intent.

Before an engineer decides **how** to perform work, the engineer must understand **why** the work exists.

Correctly identifying engineering intent reduces unnecessary engineering work and improves engineering reasoning.

---

# Core Principle

Every engineering activity should have exactly one primary engineering intent.

Secondary intents may exist but should not replace the primary intent.

---

# Engineering Intent Hierarchy

Engineering Intent follows the progression of the Engineering Process.

```text
Need
    ↓
Discover
    ↓
Understand
    ↓
Define
    ↓
Design
    ↓
Validate
    ↓
Plan
    ↓
Implement
    ↓
Verify
    ↓
Learn
```

Each phase represents a different engineering intent.

---

# Engineering Intent Taxonomy

## discover_problem

Purpose

Determine whether a meaningful engineering problem or opportunity exists.

Typical questions

* What problem exists?
* Who experiences it?
* Why is it important?

---

## understand_problem

Purpose

Improve understanding of the problem domain.

Typical questions

* How does the current system work?
* What constraints exist?
* Who are the stakeholders?

---

## define_problem

Purpose

Create a precise engineering definition of the problem.

Typical questions

* What exactly should be solved?
* What is in scope?
* What defines success?

---

## design_solution

Purpose

Develop engineering solutions.

Typical questions

* What architecture should be used?
* Should another subsystem be introduced?
* Which responsibilities belong together?

---

## validate_solution

Purpose

Evaluate proposed engineering solutions before implementation.

Typical questions

* Is the design sound?
* Are risks acceptable?
* Should this proceed?

---

## plan_work

Purpose

Prepare approved engineering work for execution.

Typical questions

* What should be implemented first?
* What dependencies exist?
* How should work be sequenced?

---

## implement_solution

Purpose

Convert approved engineering knowledge into working software.

Implementation follows approved engineering artifacts.

Implementation should not redefine engineering intent.

---

## verify_solution

Purpose

Determine whether implementation satisfies engineering intent.

Typical questions

* Does it work?
* Does it satisfy requirements?
* Are quality objectives achieved?

---

## capture_learning

Purpose

Capture engineering knowledge produced through execution.

Typical questions

* What did we learn?
* Which assumptions changed?
* What knowledge should be preserved?

---

# Intent Selection Rules

Every engineering activity must identify:

* one primary intent
* zero or more secondary intents

Primary intent determines:

* Engineering Phase
* Decision Guide retrieval
* Knowledge retrieval
* Reasoning strategy

Secondary intents provide additional engineering context.

---

# Relationship to Engineering Process

Engineering Intent identifies **why** engineering work is occurring.

The Engineering Process identifies **where** that work occurs.

Engineering Intent is therefore the entry point into the Engineering Process.

---

# Relationship to ECF

The Engineering Control Framework uses Engineering Intent to:

* classify Work Requests
* retrieve engineering knowledge
* select reasoning strategies
* choose workflows
* select engineering tasks

ECF consumes the Engineering Intent Model.

It does not define it.

---

# Guiding Principle

Engineering Intent explains why engineering work exists.

Correctly identifying intent is the first engineering decision made in every execution.
