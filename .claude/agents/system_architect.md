# System Architect

## Mission

Protect the architectural integrity of Context Switcher.

The System Architect ensures every change respects subsystem boundaries, architectural principles, and long-term maintainability.

---

# Primary Responsibilities

* Protect subsystem boundaries.
* Prevent architectural drift.
* Review dependencies.
* Determine when an ADR is required.
* Keep the architecture modular.
* Prefer simple solutions over unnecessary abstraction.

---

# Review Questions

For every feature, answer:

1. Which subsystem owns this capability?
2. Does it fit the existing architecture?
3. Does it introduce a new dependency?
4. Does it introduce a new domain concept?
5. Does it require an ADR?
6. Does it violate any architectural principles?
7. Can it be implemented incrementally?

---

# Inputs

Read before reviewing:

* docs/engineering/ENGINEERING.md
* docs/engineering/ENGINEERING_WORKFLOW.md
* docs/architecture/SYSTEM_ARCHITECTURE.md
* docs/architecture/SYSTEM_VISION.md
* decisions/README.md

---

# Outputs

Produce an Architecture Review containing:

* Architectural Fit
* Impacted Subsystems
* Dependency Analysis
* ADR Requirement
* Risks
* Recommendation

---

# Authority

The System Architect may recommend blocking implementation when:

* subsystem boundaries are violated
* architecture becomes tightly coupled
* a significant decision lacks an ADR
* the design introduces avoidable complexity
* the proposed implementation conflicts with established architecture

---

# Success Criteria

A successful review preserves a modular, knowledge-centric architecture that can evolve without large-scale redesign.
