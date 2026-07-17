Engineering Recommendation Report — EXP-0004
Engineering question: Should Repository Integration become a first-class subsystem in Context Switcher?

ECF classification: Architecture decision. Retrieval intent = Make a Decision → primary object DG-ARCH-0001, per the retrieval model.

Sources: this repository, vendor/ecf, and vendor/ecf/vendor/engineering_kb only. No files modified. Statements are labeled engineering knowledge (EKB), project evidence (repo), or inference/assumption.

1. Retrieved EKB Guidance
Following the Decision Guide's declared relationships only (the EKP-ARCH-0001 closure):

Object	ID	Guidance used
Should I Introduce Another Subsystem?	DG-ARCH-0001	Three alternatives (keep / create / delay); separation heuristics; "postpone rather than introduce speculative architecture"; common mistakes incl. "optimizing for hypothetical requirements."
Coupling	CON-ARCH-0001	A split is worthwhile only if it reduces real dependencies.
Cohesion	CON-ARCH-0002	One-sentence test; parts should change for the same reasons.
Bounded Context	CON-ARCH-0003	Distinct, stable vocabulary reveals a boundary; don't define a context before understanding the domain.
Modular Architecture	PAT-ARCH-0001	Use when responsibilities are distinct and evolve independently; "avoid when boundaries are speculative."
Maintainability	QA-0001	The upside a well-placed boundary buys.
Complexity	QA-0002	A premature boundary relocates complexity and adds coordination cost.
Subsystem Split Examples	EX-ARCH-0001	"Delay the split" case: unclear vocabulary/responsibilities → keep together, gather evidence.
2. Application to Project Context
Project evidence — a home already exists. SYSTEM_ARCHITECTURE.md already places repository work inside two established subsystems: the Integration subsystem lists "Local Git repositories" as an external-system example (responsibility: "connect to external systems"), and the AI subsystem lists "Repository evaluation" as a responsibility (AI may depend on Integration). ADR-0004 already reserves the integration events RepositoryOpened and RepositoryScanCompleted. So repository integration is not homeless — it is already decomposed across mature boundaries.

Testing DG-ARCH-0001's separation heuristics against the modified context:

Heuristic	Verdict
One primary responsibility	Unclear — project: "Repository integration scope" unresolved; connectivity (Integration) vs. evaluation (AI) not yet delineated.
Own, stable vocabulary	No — modified context: "Local Git vs GitHub API unresolved"; CON-ARCH-0003 warns against fixing a context before the domain is understood.
Changes for independent reasons	Unknown — modified context: "no observed change patterns exist."
Independently testable / hidden internals	Already satisfied by the existing Integration/AI boundaries — argues for current placement, not a new one.
Expected future growth	Yes (work-session evaluation is in the mission) — but DG-ARCH-0001 flags "optimizing for hypothetical requirements" as a mistake.
Consolidation/delay forces stacked by the modified context: MVP unimplemented; repository integration not in MVP; scope + vocabulary unresolved; no change patterns; "delivery speed and simplicity matter"; "architecture should avoid speculative boundaries." Every one of these maps to the EKB's consolidation column and to PAT-ARCH-0001's explicit "avoid when boundaries are speculative." ADR-0002 independently mandates "start with modular boundaries, not a full plugin system" and already names the future review trigger — "external integrations become central to the product" — which has not fired.

The closest EKB analogue is EX-ARCH-0001's "delay the split": a capability whose vocabulary and responsibilities are still unclear → keep it in place and gather evidence.

3. Decision
Keep Repository Integration inside the existing Integration subsystem — do NOT introduce a first-class subsystem — and defer any promotion until evidence exists.

Answer to the question: No, not now. "Keep" is the positive placement (Integration already owns external connectivity; AI already owns evaluation); "defer" governs the promotion question, to be reopened when the open questions resolve or first implementation reveals change patterns. Introducing a subsystem today would, in the EKB's own terms, be "introducing architecture without a responsibility boundary" and "optimizing for hypothetical requirements" — with a boundary that is "one of the most expensive to change later."

4. Trade-offs
Maintainability vs. Complexity (QA-0001 / QA-0002): a correctly placed boundary later raises maintainability; creating it now would only relocate complexity and add coordination across Integration ↔ new ↔ AI — with no dependency reduction to show for it (CON-ARCH-0001: "splitting without reducing real dependencies achieves nothing").
Cohesion (CON-ARCH-0002): the one-sentence test fails while scope is open; a premature split risks low cohesion on both sides.
Delivery (project constraint): keeping placement as-is directly serves "delivery speed and simplicity."
Cost of the recommendation: if repository integration later proves to be a genuine bounded context (e.g., GitHub API grows rich, distinct rules emerge), the Integration subsystem will have grown and a split will be needed then — but that split is cheaper and better-informed once change patterns are observable. The re-evaluation trigger below bounds this risk.
Constraint alignment: leaving evaluation inside the AI boundary preserves the repo's AI-provider-independent and knowledge-first constraints.
5. Confidence
High that promotion now is unwarranted; Medium on the eventual long-term boundary.

High (near-term): every consolidation/delay force in DG-ARCH-0001 is present and reinforced by the modified context and by ADR-0002; the decision is low-regret and reversible; a concrete home already exists in the repo.
Capped at Medium (long-term): DG-ARCH-0001 reserves high confidence for boundaries "supported by observed change patterns," which by stipulation do not exist; the "Local Git vs GitHub API" scope could still shift the bounded context. All EKB source objects are draft, confidence: medium, so guidance is provisional.
6. Missing Information & Next Step
Resolve before revisiting: (1) repository integration scope — connectivity only vs. connectivity + evaluation; (2) Local Git vs GitHub API (settles vocabulary); (3) repository evaluation evidence requirements and AI recommendation boundaries; (4) first observed change patterns once implementation begins.

Suggested next ECF transformation: capture this as a short ADR ("Repository Integration remains within the Integration and AI subsystems; revisit on the ADR-0002 trigger"), then run a Requirements/Product Design Transformation on Repository-Aware Work Evaluation to answer the open questions — the evidence that a future re-run of DG-ARCH-0001 would need.

Distinctions maintained: engineering knowledge = EKB objects; project evidence = repository artifacts; inference/assumption and decision labeled inline. No project facts invented; no files modified.