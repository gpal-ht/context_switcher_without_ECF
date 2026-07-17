EXP-0003 — Cohesion Ablation
Simulated in memory via the engine; no repository files were modified. Removing CON-ARCH-0002 from the loaded graph and re-running retrieval + validation produced the results below.

Retrieved Objects
With Cohesion excluded, retrieval from DG-ARCH-0001 yields 7 objects (down from 8):

ID	Title	Type	Status
DG-ARCH-0001	Should I Introduce Another Subsystem?	decision_guide	retained
CON-ARCH-0001	Coupling	engineering_concept	retained
CON-ARCH-0003	Bounded Context	engineering_concept	retained
PAT-ARCH-0001	Modular Architecture	engineering_pattern	retained
QA-0001	Maintainability	quality_attribute	retained
QA-0002	Complexity	quality_attribute	retained
EX-ARCH-0001	Subsystem Split Examples	example	retained
Missing Object
CON-ARCH-0002 — Cohesion (engineering_concept).

Cohesion is the most cross-referenced node in this closure. Removing it leaves 6 broken references — one from every other object type in the package:

Source	Relationship	Consequence of loss
DG-ARCH-0001	requires → CON-ARCH-0002	The Decision Guide declares a hard dependency on Cohesion. The primary object is now incomplete by its own declaration.
CON-ARCH-0003 (Bounded Context)	related_to	Bounded-context reasoning loses its link to responsibility relatedness.
PAT-ARCH-0001 (Modular Architecture)	requires	The pattern's foundation is half-missing; it requires both Coupling and Cohesion.
QA-0001 (Maintainability)	supported_by	The causal chain "high cohesion → maintainability" is severed.
QA-0002 (Complexity)	affected_by	The link "low cohesion → higher complexity" is severed.
EX-ARCH-0001 (Subsystem Split Examples)	illustrates	The examples explicitly demonstrate cohesion; the demonstration now has no concept to point to.
Validation of the ablated graph: FAILED — 6 errors.

Degraded Reasoning
Coupling and Cohesion are co-equal, complementary primitives. Coupling reasons about dependencies between parts; Cohesion reasons about relatedness within a part. Losing Cohesion removes an entire axis of the decision:

Cannot evaluate whether a candidate subsystem is internally coherent. With only Coupling, you can confirm a boundary reduces cross-part dependencies — but nothing tells you whether the thing inside the boundary is one responsibility or a grab-bag. A low-coupling, low-cohesion subsystem (unrelated responsibilities behind a clean interface) would pass the remaining checks yet be a bad boundary. That failure mode becomes invisible.
The core "is this really one subsystem?" tests disappear. Cohesion supplies the decisive heuristics: do these responsibilities belong together, do they change for the same reasons, can the subsystem be explained in one sentence. The DG's heuristics ("one primary responsibility," "changes independently") lean directly on these and are left unsupported.
The "poor split" example can no longer be explained. EX-ARCH-0001's poor case — splitting one button into rendering/state/styling subsystems — is precisely a cohesion failure: responsibilities that belong together were torn apart. Without Cohesion, the package can still show the example but cannot articulate why it is wrong.
The quality-attribute causality is broken. Both Maintainability and Complexity are declared to depend on Cohesion. The package can still name the qualities but can no longer trace how the boundary decision moves them — reducing the guidance to assertion rather than reasoning.
Bounded Context is weakened. Bounded Context is related_to Cohesion; distinguishing a natural context partly rests on responsibilities cohering. That supporting link is gone.
Net effect: the package degrades from "reason to a decision" to "reason about dependencies only." Roughly half the decision framework — the entire internal-coherence axis — is lost.

Sufficiency Result
NOT sufficient.

The primary Decision Guide requires Cohesion; a package missing a requires dependency of its own primary object fails the retrieval model's completeness criterion by construction.
Acceptance test RAT-ARCH-0001 fails: a required supporting Concept is absent.
Human-validation criterion fails: an experienced engineer cannot fully reason about a subsystem boundary from the retrieved set — they could assess coupling but not internal cohesion, and would have to supply the missing concept from outside EKB, which the model forbids.
This ablation confirms Cohesion is load-bearing, not decorative: its removal is felt across every object type in the closure, not just locally.

Recommendation for EKB
Treat requires edges from a primary object as sufficiency-critical. If any requires target is missing, the package should be reported INSUFFICIENT, not merely "smaller." Consider having the engine's package generation fail hard (non-zero) when a primary's requires closure is incomplete.
Add a sufficiency gate to the engine. Extend validate/retrieve with a check: for the primary object, every requires (and ideally illustrated_by) target must resolve. Surface a one-line SUFFICIENCY: PASS/FAIL verdict in retrieve output.
Flag high-centrality objects. Cohesion is referenced 6 ways; such hubs are single points of failure for package quality. A simple report of in-degree per object would let authors see which removals would be most damaging before editing.
Keep Coupling and Cohesion paired in authoring guidance. Because they form one reasoning axis together, the authoring guide should warn against shipping a decision guide that requires one without the other.
Preserve the ablation as a regression test. Add a negative acceptance test (e.g. RAT-ARCH-0001-ABLATE-COHESION) asserting that removing CON-ARCH-0002 makes the package fail sufficiency — locking in the finding that Cohesion is required.