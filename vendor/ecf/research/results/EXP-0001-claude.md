EXP-0001 — Engineering Knowledge Package
Generated from canonical EKB objects. No files were modified. Retrieval performed by engine/ekb.py (traversal of declared relationships only, scoped to a single decision guide).

Question
Should I introduce another subsystem?

Retrieval Path
Traversal began at the Decision Guide and followed declared relationships only. No object outside this relationship closure was included.

DG-ARCH-0001  (Should I Introduce Another Subsystem?)
├─ requires        → CON-ARCH-0001  (Coupling)
├─ requires        → CON-ARCH-0002  (Cohesion)
├─ requires        → CON-ARCH-0003  (Bounded Context)
│                     └─ related_to → CON-ARCH-0001, CON-ARCH-0002
├─ supports        → QA-0001        (Maintainability)
├─ supports        → QA-0002        (Complexity)
├─ references      → PAT-ARCH-0001  (Modular Architecture)
│                     ├─ requires  → CON-ARCH-0001, CON-ARCH-0002
│                     ├─ optimizes → QA-0001
│                     └─ affects   → QA-0002
└─ illustrated_by  → EX-ARCH-0001  (Subsystem Split Examples)
                      └─ illustrates → DG-ARCH-0001, CON-ARCH-0001, CON-ARCH-0002, PAT-ARCH-0001
Second-level edges resolve entirely within the set already reached from the Decision Guide — the closure is complete and self-contained. Traversal deliberately did not hop into any other Decision Guide.

Retrieved Objects
ID	Title	Type	Discovered via
DG-ARCH-0001	Should I Introduce Another Subsystem?	decision_guide	primary
CON-ARCH-0001	Coupling	engineering_concept	requires
CON-ARCH-0002	Cohesion	engineering_concept	requires
CON-ARCH-0003	Bounded Context	engineering_concept	requires
PAT-ARCH-0001	Modular Architecture	engineering_pattern	references
QA-0001	Maintainability	quality_attribute	supports
QA-0002	Complexity	quality_attribute	supports
EX-ARCH-0001	Subsystem Split Examples	example	illustrated_by
8 objects retrieved. Matches acceptance test RAT-ARCH-0001 exactly (correct primary, all required supporting objects, no unrelated knowledge).

Executive Summary
A subsystem boundary is among the most expensive architectural decisions to reverse, so it should be driven by a clear responsibility boundary — not by folder layout, file size, or speculative future needs. The decision rests on three reasoning primitives: coupling (how strongly parts depend on one another), cohesion (how related the responsibilities inside a part are), and bounded context (a boundary within which vocabulary and rules stay consistent). A well-placed boundary raises maintainability and can lower complexity; a premature one merely relocates complexity and adds coordination cost. Modular Architecture is the pattern that operationalizes a sound boundary once the responsibility is genuinely understood. When understanding is incomplete, the guide favors delaying the split over introducing speculative structure.

Decision Guidance
(from DG-ARCH-0001 — general engineering guidance, not a project-specific verdict)

The decision surfaces when a growing capability begins to look distinct from its surroundings, signaled by increasing implementation complexity, different reasons for change, growing responsibility boundaries, and rising coordination between unrelated concepts.

Three recognized alternatives:

Keep the capability within the existing subsystem — appropriate when responsibilities remain closely related, implementation is still evolving, or boundaries are not yet understood. Lower immediate complexity, but risks future coupling and an ever-growing subsystem.
Create a separate subsystem — appropriate when the responsibility is clearly defined, change patterns differ, and boundaries are stable. Improves modularity, ownership, testing, and reasoning, at the cost of coordination and possible over-engineering.
Delay the decision — appropriate when engineering understanding is still incomplete; intentionally gathers evidence before restructuring.
Decision heuristics favor a separate subsystem when most hold: one primary responsibility, independent reasons to change, its own vocabulary, independent testability, hidden internal implementation, and expected future growth. If these are not yet understood, postpone rather than introduce speculative architecture.

Common mistakes: splitting on folder structure, splitting because a file grew large, introducing architecture without a responsibility boundary, optimizing for hypothetical requirements, and treating every capability as a subsystem.

Concepts
Coupling (CON-ARCH-0001) — how strongly one part depends on another. Low coupling lets a component change with limited impact; high coupling causes changes to ripple. Subsystem boundaries are often introduced specifically to reduce harmful coupling. Key checks: what must one component know about another, can one change without forcing the other, and are implementation details leaking across boundaries. Not all coupling is bad, and splitting code without reducing real dependencies achieves nothing.

Cohesion (CON-ARCH-0002) — how closely related the responsibilities inside a part are. Subsystems should usually have high cohesion; grouping unrelated responsibilities makes a subsystem hard to understand, test, and evolve. A useful test: do these responsibilities naturally belong together, do they change for the same reasons, and can the subsystem be explained clearly in one sentence.

Bounded Context (CON-ARCH-0003) — a boundary within which a model, vocabulary, and rules stay consistent. Distinct vocabulary and differing rules often reveal a natural subsystem boundary. Related to both coupling and cohesion. Pitfalls: defining contexts before understanding the domain, assuming every feature is its own context, and ignoring vocabulary conflicts.

Pattern
Modular Architecture (PAT-ARCH-0001) organizes a system into parts with clear responsibilities and controlled dependencies, each hiding internal detail behind a clear boundary. It lets engineers reason about one part without understanding everything else. It requires the coupling and cohesion concepts, optimizes maintainability, and affects complexity.

Benefits: clearer ownership, better maintainability, easier testing, localized change.
Costs: more boundaries to manage, possible over-abstraction, inter-module coordination.
Use when responsibilities are distinct and likely to evolve independently; avoid when boundaries are speculative or the system is still too small to justify the structure.
Quality Attributes
Maintainability (QA-0001) — the ease of understanding, changing, testing, and safely evolving software. Since most software cost occurs after initial implementation, maintainability governs the cost and risk of future change. It improves with clear responsibilities, controlled coupling, high cohesion, low-setup tests, and localized change; it degrades when concerns are mixed, details leak across boundaries, or small changes require broad edits. (supported_by DG-ARCH-0001, CON-ARCH-0001, CON-ARCH-0002)

Complexity (QA-0002) — the mental effort required to understand, change, and verify a system. Complexity increases engineering risk. Subsystems can reduce it through clear boundaries, but can increase it if introduced prematurely. The governing question is whether a design reduces reasoning effort or merely moves complexity around. (affected_by DG-ARCH-0001, CON-ARCH-0001, CON-ARCH-0002)

Examples
(from EX-ARCH-0001)

Good split — a desktop productivity app separates work-session timing, persistent project knowledge, and AI recommendations into Work, Knowledge, and AI subsystems. These change for different reasons; the split gives clear responsibilities, controllable coupling, easier testing, and distinct vocabularies.
Poor split — a one-screen app with three buttons split into rendering, state, and styling subsystems. The split reduces no reasoning cost, increases coordination, and introduces premature abstraction — complexity rises with no benefit.
Delay the split — a growing feature whose vocabulary and responsibilities are still unclear. Keeping the code together while gathering evidence is the better choice when the boundary is not yet understood.
Sufficiency Statement
The retrieved set is self-contained for reasoning about this decision. It provides the decision framework (DG-ARCH-0001), the three concepts it depends on (coupling, cohesion, bounded context), the pattern that realizes a sound boundary (modular architecture), both quality attributes the decision drives (maintainability, complexity), and concrete good/poor/delay examples. Every declared relationship resolves within the package, and the closure matches acceptance test RAT-ARCH-0001. An experienced engineer can reason to a decision using only these objects, with no external references required.

Limitations
This package presents general engineering knowledge and deliberately renders no verdict on any specific project (per instruction 4).
Scope is limited to the canonical relationship closure of DG-ARCH-0001; no security, deployment, testing-strategy, accessibility, or unrelated design-pattern knowledge is included, because none is connected via declared relationships.
All source objects are status: draft, version 0.1.0, confidence: medium — guidance should be treated as provisional.
Minor source defect (not modified): CON-ARCH-0001 (Coupling) ends with a stray typo — "dependencies.s". It does not affect relationships or reasoning.
Source inconsistency (not modified): DG-ARCH-0001 declares type: decision_guide, whereas KNOWLEDGE_OBJECT_STANDARD.md prescribes type: engineering_decision. It does not affect retrieval.
Experiment result: PASS. EKB generated a complete, human-readable Engineering Knowledge Package by starting at the relevant Decision Guide, traversing declared relationships only, and reporting its retrieval path and sources — with no project-specific recommendation and no files modified.