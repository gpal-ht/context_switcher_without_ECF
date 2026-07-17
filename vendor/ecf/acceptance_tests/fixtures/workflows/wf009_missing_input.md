---
workflow_id: WF-FX09-0001
name: Fixture
version: 0.1.0
status: draft
category: test
owner: engineering_control_framework
entry_state: accepted
successful_exit_state: completed
---

# Stable Output Bindings

| Task ID | Version | Bound primary output |
|---|---|---|
| TASK-CLASSIFY-0001 | 0.1.0 | `task_outputs/a.yaml` |

# Task Graph

## Step 1 — Build
* Task: TASK-CLASSIFY-0001 @ 0.1.0
* Upstream: none (entry)
* Required inputs: `ghost-input.yaml`
