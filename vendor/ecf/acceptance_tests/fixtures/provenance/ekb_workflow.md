---
workflow_id: WF-EKB-0001
name: EKB Consumer
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
| TASK-RETRIEVE-0002 | 0.1.0 | `task_outputs/engineering-knowledge-package.md` |

# Deps

```yaml
depends_on:
  TASK-RETRIEVE-0002: []
```

# Environment Dependencies

```yaml
environment_dependencies:
  default:
    ecf: required
    ekb: not_required
  TASK-RETRIEVE-0002:
    ecf: required
    ekb: required
```
