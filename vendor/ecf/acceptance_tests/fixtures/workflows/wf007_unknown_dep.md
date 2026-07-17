---
workflow_id: WF-FX07-0001
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
| TASK-CLASSIFY-0002 | 0.1.0 | `task_outputs/b.yaml` |

# Deps

```yaml
depends_on:
  TASK-CLASSIFY-0001: []
  TASK-CLASSIFY-0002:
    - TASK-GHOST-9999
```
