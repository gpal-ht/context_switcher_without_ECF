# Engineering Control Framework (ECF)

> **A reusable engineering governance framework for building high-quality software with humans and AI working together.**

## Purpose

Engineering Control Framework (ECF) provides a structured approach to software engineering by standardizing:

* engineering principles
* engineering workflows
* engineering activities
* engineering artifacts
* review processes
* quality gates
* AI participation

ECF is designed to ensure that engineering quality is driven by explicit standards and repeatable processes rather than ad hoc prompts or individual expertise.

---

# Why ECF?

Modern AI systems can generate code rapidly.

However, software quality depends far more on the quality of engineering decisions than on the speed of implementation.

ECF exists to improve decision quality before implementation begins.

Its objective is to help engineering teams produce software that is:

* understandable
* maintainable
* testable
* secure
* accessible
* explainable
* reviewable

---

# Core Philosophy

ECF follows a simple principle:

> **Control the engineering process, and the quality of the software will follow.**

Implementation is the result of engineering—not its starting point.

---

# Who Is ECF For?

ECF is intended for:

* individual developers
* AI-assisted software projects
* engineering teams
* software architects
* technical leads
* organizations adopting AI-assisted development

It is independent of:

* programming language
* framework
* platform
* cloud provider
* AI vendor

---

# Framework Structure

ECF is organized into eight pillars.

1. Principles
2. Standards
3. Workflows
4. Activities
5. Artifacts
6. Reviews
7. Quality Gates
8. AI Execution

Each pillar has a single responsibility and builds upon the previous one.

---

# Repository Structure

```text
knowledge/
    Engineering knowledge and reference material

principles/
    Engineering principles and philosophy

standards/
    Definitions of engineering quality

workflows/
    Repeatable engineering processes

activities/
    Engineering activities and their specifications

artifacts/
    Engineering artifact definitions

templates/
    Reusable templates for artifacts

review_packs/
    Standard review combinations

quality_gates/
    Definitions of Ready, Done, and approval gates

agents/
    AI role definitions

examples/
    Example projects using ECF
```

---

# Engineering Lifecycle

Every significant piece of work follows the same lifecycle.

```text
Intent
    ↓
Workflow
    ↓
Activities
    ↓
Artifacts
    ↓
Reviews
    ↓
Quality Gates
    ↓
Implementation
    ↓
Verification
    ↓
Knowledge Capture
```

---

# Design Goals

ECF is designed to be:

* modular
* provider-independent
* versioned
* reusable
* scalable
* explainable
* deterministic where practical

---

# Relationship to AI

AI is treated as an engineering participant.

AI follows the framework.

AI does not define the framework.

Human approval remains the final authority for engineering decisions.

---

# Current Status

Current version:

**ECF v0.1**

Primary focus:

* establish engineering philosophy
* define framework architecture
* standardize engineering workflows
* define reusable engineering artifacts

---

# Validating Workflows

Workflow specifications can be mechanically checked (read-only, no execution) with the conformance validator:

```powershell
# One workflow
python tools/workflow_validator/validate_workflow.py workflows/reasoning/WF-REASON-0001-engineering-recommendation.md

# All applicable workflows from the catalog
.\scripts\validate-workflows.ps1
```

See `tools/workflow_validator/README.md`. This validates the ECF control plane; it does not execute engineering reasoning.

Create a schema-valid, planner-ready runtime run from a workflow + a Work Request (no task execution, no AI):

```powershell
python tools/run_initializer/initialize_run.py workflows/reasoning/WF-REASON-0001-engineering-recommendation.md `
  --work-request work_requests/WR-0001.md --run-root runtime/runs --run-id RUN-REASON-WR0001-0001

# PowerShell wrapper (resolves ECF root from its own location; canonical or vendored):
.\scripts\initialize-run.ps1 -WorkRequest work_requests\WR-0001.md -RunId RUN-REASON-WR0001-0001
```

See `tools/run_initializer/README.md`. The initializer writes only the initial run; the runtime transaction layer remains the sole writer thereafter.

Compute what could run next, and detect stale outputs (read-only):

```powershell
# Which tasks are runnable now (optionally against a run directory)?
python tools/workflow_planner/plan_workflow.py workflows/reasoning/WF-REASON-0001-engineering-recommendation.md --run runtime/runs/<RUN_ID>

# SHA-256 fingerprint of a runtime artifact
python -m tools.artifact_fingerprint.fingerprint runtime/runs/<RUN_ID>/task_outputs/engineering-forces.yaml
```

Inspect runtime-state consistency (read-only; the runtime transaction layer is the sole writer):

```powershell
python tools/runtime_state/recovery.py runtime/runs/<RUN_ID>
.\scripts\inspect-runtime-state.ps1 -RunDir runtime\runs\<RUN_ID>
```

Execute exactly one planner-approved task (fixture executor, or the opt-in AI executor for `TASK-CLASSIFY-0001`):

```powershell
# safe fixture executor
python tools/task_runner/run_task.py workflows/reasoning/WF-REASON-0001-engineering-recommendation.md `
  --run runtime/runs/<RUN_ID> --task TASK-CLASSIFY-0001 --executor fixture --fixture <candidate-output>

# AI-backed intent classification (disabled by default; requires explicit opt-in)
.\scripts\run-intent-task-with-claude.ps1 -Run runtime\runs\<RUN_ID>
```

See `tools/run_initializer/README.md`, `tools/workflow_planner/README.md`, `tools/artifact_fingerprint/README.md`, `tools/runtime_state/README.md`, `tools/task_runner/README.md`, and `runtime_schemas/` (`TASK_PROVENANCE_SCHEMA.md`, `RUN_STATE_SCHEMA.md`, `RUN_MANIFEST_SCHEMA.md`, `RUNTIME_TRANSACTION_CONTRACT.md`, `ENGINEERING_INTENT_RESULT_SCHEMA.md`).

---

# Related Projects

ECF is intended to be adopted by software projects.

The first reference implementation is:

* Context Switcher

Future projects should adopt ECF rather than duplicate engineering governance.

---

# License

To be determined.
