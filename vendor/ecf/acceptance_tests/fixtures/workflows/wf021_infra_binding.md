---
workflow_id: WF-FX21-0001
name: Fixture
version: 0.1.0
status: draft
category: test
owner: engineering_control_framework
entry_state: accepted
successful_exit_state: completed
---

# Stable Output Bindings

A task output bound to the runtime-owned `manifest.yaml` must be rejected (WF021).

| Task ID | Version | Bound primary output |
|---|---|---|
| TASK-CLASSIFY-0001 | 0.1.0 | `task_outputs/engineering-intent.yaml` |
| TASK-CLASSIFY-0002 | 0.1.0 | `manifest.yaml` |
