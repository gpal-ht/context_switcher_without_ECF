# ENGINEERING_KNOWLEDGE_PACKAGE.md

# Purpose

An Engineering Knowledge Package is the human-readable and machine-readable output of an Engineering Knowledge Base retrieval.

It is the stable interface between EKB and ECF.

EKB does not return raw search results.

EKB returns a curated package of engineering guidance.

---

# Core Principle

A Knowledge Package must show:

1. What engineering question was asked.
2. Which knowledge objects were retrieved.
3. Why those objects were selected.
4. What guidance they provide.
5. What evidence supports the guidance.

---

# Package Structure

## 1. Package Metadata

Required fields:

```yaml
---
package_id: EKP-ARCH-0001
question: Should I introduce another subsystem?
intent: make_decision
status: draft
created: YYYY-MM-DD
source_test: RAT-ARCH-0001
primary_object: DG-ARCH-0001
retrieved_objects:
  - DG-ARCH-0001
  - CON-ARCH-0001
  - CON-ARCH-0002
  - CON-ARCH-0003
  - PAT-ARCH-0001
  - QA-0001
  - QA-0002
  - EX-ARCH-0001
---