# DECISION_GUIDE_CATALOG.md

# Purpose

This catalog defines the Engineering Decision Guides that collectively form the Engineering Knowledge Base (EKB).

Decision Guides are the primary entry point into EKB.

Every Decision Guide should answer a recurring engineering question that experienced engineers regularly face.

Supporting knowledge (Concepts, Patterns, Quality Attributes, Examples, References) exists to help engineers reason about these decisions.

This catalog serves as the roadmap for the growth of EKB.

---

# Decision Guide Philosophy

Decision Guides should represent:

* recurring engineering decisions
* technology-independent reasoning where practical
* reusable engineering judgment
* decisions with meaningful trade-offs
* questions whose answers improve engineering quality

Decision Guides should **not** represent:

* implementation tutorials
* API documentation
* framework-specific instructions
* programming language syntax
* one-off project decisions

---

# Engineering Disciplines

## Product Engineering

| ID           | Decision Guide                       | Priority | Status  |
| ------------ | ------------------------------------ | -------: | ------- |
| DG-PROD-0001 | Should this capability exist?        |     High | Planned |
| DG-PROD-0002 | Should this belong in the MVP?       |     High | Planned |
| DG-PROD-0003 | Should this feature be split?        |     High | Planned |
| DG-PROD-0004 | Should this requirement be deferred? |   Medium | Planned |

---

## Requirements Engineering

| ID          | Decision Guide                              | Priority | Status  |
| ----------- | ------------------------------------------- | -------: | ------- |
| DG-REQ-0001 | Is this a requirement or a design decision? |     High | Planned |
| DG-REQ-0002 | Is this requirement complete?               |     High | Planned |
| DG-REQ-0003 | Should this requirement be split?           |     High | Planned |
| DG-REQ-0004 | Is this requirement testable?               |     High | Planned |
| DG-REQ-0005 | Is this requirement measurable?             |   Medium | Planned |

---

## Architecture

| ID           | Decision Guide                                    | Priority | Status   |
| ------------ | ------------------------------------------------- | -------: | -------- |
| DG-ARCH-0001 | Should I introduce another subsystem?             |     High | Complete |
| DG-ARCH-0002 | Should I introduce another layer?                 |     High | Planned  |
| DG-ARCH-0003 | Should this capability become a separate service? |     High | Planned  |
| DG-ARCH-0004 | Should I use event-driven architecture?           |     High | Planned  |
| DG-ARCH-0005 | Should I introduce an abstraction?                |     High | Planned  |
| DG-ARCH-0006 | Should I create an interface?                     |     High | Planned  |
| DG-ARCH-0007 | Should I adopt a plugin architecture?             |   Medium | Planned  |
| DG-ARCH-0008 | Should I introduce a cache?                       |   Medium | Planned  |

---

## Design

| ID             | Decision Guide                              | Priority | Status  |
| -------------- | ------------------------------------------- | -------: | ------- |
| DG-DESIGN-0001 | Should I use composition or inheritance?    |     High | Planned |
| DG-DESIGN-0002 | Should this object own this responsibility? |     High | Planned |
| DG-DESIGN-0003 | Should this become a separate class?        |     High | Planned |
| DG-DESIGN-0004 | Should this dependency be injected?         |   Medium | Planned |

---

## Runtime

| ID              | Decision Guide                         | Priority | Status  |
| --------------- | -------------------------------------- | -------: | ------- |
| DG-RUNTIME-0001 | Should this state be persisted?        |     High | Planned |
| DG-RUNTIME-0002 | Should this operation be asynchronous? |     High | Planned |
| DG-RUNTIME-0003 | Should this become an event?           |     High | Planned |
| DG-RUNTIME-0004 | Should this operation be recoverable?  |     High | Planned |

---

## Data

| ID           | Decision Guide                     | Priority | Status  |
| ------------ | ---------------------------------- | -------: | ------- |
| DG-DATA-0001 | Should this data be persisted?     |     High | Planned |
| DG-DATA-0002 | Should this be normalized?         |   Medium | Planned |
| DG-DATA-0003 | Should this become its own entity? |     High | Planned |

---

## Testing

| ID           | Decision Guide                      | Priority | Status  |
| ------------ | ----------------------------------- | -------: | ------- |
| DG-TEST-0001 | Should this be a unit test?         |     High | Planned |
| DG-TEST-0002 | Should this be an integration test? |     High | Planned |
| DG-TEST-0003 | Is this worth automating?           |   Medium | Planned |
| DG-TEST-0004 | What should be mocked?              |     High | Planned |

---

## Security

| ID          | Decision Guide                              | Priority | Status  |
| ----------- | ------------------------------------------- | -------: | ------- |
| DG-SEC-0001 | Should this data leave the device?          |     High | Planned |
| DG-SEC-0002 | Where is the trust boundary?                |     High | Planned |
| DG-SEC-0003 | Should this data be encrypted?              |     High | Planned |
| DG-SEC-0004 | Does this operation require authentication? |     High | Planned |

---

## Accessibility

| ID           | Decision Guide                           | Priority | Status  |
| ------------ | ---------------------------------------- | -------: | ------- |
| DG-A11Y-0001 | Is this interaction keyboard accessible? |     High | Planned |
| DG-A11Y-0002 | Is this information perceivable?         |     High | Planned |
| DG-A11Y-0003 | Should this animation be optional?       |   Medium | Planned |

---

## Performance

| ID           | Decision Guide                              | Priority | Status  |
| ------------ | ------------------------------------------- | -------: | ------- |
| DG-PERF-0001 | Is optimization justified?                  |     High | Planned |
| DG-PERF-0002 | Should this computation be cached?          |   Medium | Planned |
| DG-PERF-0003 | Is this performance measurement meaningful? |   Medium | Planned |

---

# Status Values

| Status      | Meaning                                           |
| ----------- | ------------------------------------------------- |
| Planned     | Identified but not authored                       |
| In Progress | Currently being authored                          |
| Complete    | Decision Guide exists and passes acceptance tests |
| Reviewed    | Reviewed and approved                             |
| Deprecated  | Superseded by another Decision Guide              |

---

# Completion Criteria

A Decision Guide is considered **Complete** only when:

* the Decision Guide exists
* supporting Concepts exist
* supporting Patterns exist (if applicable)
* supporting Quality Attributes exist
* supporting Examples exist
* retrieval acceptance tests pass
* Engineering Knowledge Package generation succeeds

---

# Roadmap Principle

The Engineering Knowledge Base grows by completing Decision Guides—not by accumulating isolated documents.

Each completed Decision Guide expands the engineering reasoning capability of the framework.
