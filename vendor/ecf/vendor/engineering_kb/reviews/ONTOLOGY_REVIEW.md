# ONTOLOGY_REVIEW.md

*Architecture review only. No standards, code, tests, packages, or knowledge
objects were modified. No migration was performed. This document is advisory.*

---

## Executive Summary

The canonical `type` for a DG-* object was recently standardized to
`engineering_decision`. This review evaluates, from first principles, whether
that is the right ontology.

**Finding:** `engineering_decision` models the object's **subject/purpose** (the
decision it helps make) rather than the object's **identity** (what it *is*). Every
sibling type in EKB — `engineering_concept`, `engineering_pattern`, `example`,
`quality_attribute`, `reference` — names the *artifact*. A DG-* object is not a
decision; it is a reusable, verdict-free **guide** to a recurring decision. The
standards, catalog, model, authoring guide, retrieval model, and ID prefix all
call it a **Decision Guide**. Only the `type` field disagrees.

**Recommendation:** the artifact-identity value **`type: decision_guide`**
(Candidate B) is ontologically more correct and more extensible than
`engineering_decision` (Candidate A). Reserve `engineering_decision` for a
genuinely different future object — a *record of an actual decision* (an ADR),
which EKB does not currently store. Keep retrieval *intent* (make-a-decision)
where it already lives — in the retrieval model — rather than encoding purpose in
`type`.

The previous migration correctly fixed an **inconsistency** (one value
everywhere) but standardized on the **less correct value**. Because only one DG
object exists and no ECF bundle has consumed the type yet, **now is the cheapest
possible moment to correct course** — materially cheaper than after ECF adoption.

This is a review; it does not authorize the change. Adopting it would require a
standards update first, then a small migration.

---

## Current Model

```yaml
type: engineering_decision   # ID prefix: DG-, human name: "Decision Guide"
```

Observed facts from the repository:

- **Sibling types name artifacts:** `engineering_concept`, `engineering_pattern`,
  `quality_attribute`, `example`, `reference`. Each answers *"what is this
  object?"* with a noun for the artifact.
- **Everything except the `type` field calls it a "Decision Guide":**
  `DECISION_GUIDE_STANDARD.md`, `DECISION_GUIDE_MODEL.md`,
  `DECISION_GUIDE_CATALOG.md`, `DECISION_GUIDE_AUTHORING_GUIDE.md`, the `DG-`
  prefix, and the retrieval model's primary object ("Decision Guide").
- **The object is explicitly not a decision:** the standards require it to be
  technology-neutral, reusable across projects, and to *teach reasoning without
  rendering a project-specific verdict*. Generated packages state they present
  "general engineering knowledge and deliberately do not render a verdict."
- **EKB vs ECF boundary:** "EKB teaches engineers how to reason about decisions.
  ECF defines how engineering decisions are incorporated into workflows."
  (`DECISION_GUIDE_MODEL.md`). "EKB returns a curated package of engineering
  guidance" (`ENGINEERING_KNOWLEDGE_PACKAGE.md`).

So the object is a **decision-support artifact**. `engineering_decision` names the
*thing the guide is about*, not the guide — the same category error as typing an
`example` object by the concept it illustrates.

---

## Alternative Models

**Candidate A — `type: engineering_decision`** (current)
Names the purpose/subject. Prescribed by current standards.

**Candidate B — `type: decision_guide`** (artifact identity)
Names the artifact, parallel to the sibling types. Matches the `DG-` prefix and
every other document in the repo.

**Candidate C — two-axis (artifact + purpose)**
```yaml
artifact_type: decision_guide            # what it IS
purpose: decision_support                # what it is FOR
```
or `object_type: decision_guide` + `intent: make_decision`. Separates identity
from purpose explicitly.

**Candidate D — reserve-and-distinguish (a refinement of B)**
`type: decision_guide` for reusable guides **and** reserve `engineering_decision`
as a *distinct future type* for actual decision **records** (ADRs) if EKB ever
stores project-specific decisions. Treats "guide" and "decision" as two different
objects, which they are.

---

## Evaluation Matrix

Scale: ✔✔ strong · ✔ adequate · ✖ weak.

| Criterion | A `engineering_decision` | B `decision_guide` | C two-axis |
|---|:--:|:--:|:--:|
| **Object identity** — does `type` say what it *is*? | ✖ (names the subject) | ✔✔ | ✔✔ |
| **Engineering semantics** — artifact, not purpose? | ✖ | ✔✔ | ✔ (identity ok; extra purpose field) |
| **Future extensibility** — Checklists, Threat Models, Decision Trees, Risk Models, Reference Architectures, Review Packs, Standards | ✖ (all are decision-support → collide in one purpose bucket) | ✔✔ (each gets its own artifact noun) | ✔✔ |
| **Retrieval semantics** — clearer? | ✖ (retrieval model already says "Decision Guide") | ✔✔ | ✔ |
| **Package semantics** — easier to understand? | ✖ (package holds guidance, not a decision) | ✔✔ | ✔ |
| **ECF consumption** — matches "decision-support artifact"? | ✖ (implies ECF consumes decisions) | ✔✔ | ✔✔ |
| **Human understanding** — instantly clear to an engineer? | ✔ (recognizable but ambiguous vs an ADR) | ✔✔ | ✔ (two fields to learn) |
| **Ontology consistency** — sits beside concept/pattern/example? | ✖ (odd one out) | ✔✔ | ✔ (needs a key rename to fit) |
| **Simplicity / churn** | ✔ (status quo) | ✔✔ (value-only change) | ✖ (new key + redundant field) |

**Net:** B dominates A on every semantic axis and ties or beats C while adding no
new machinery. A's only advantage is incumbency, which this review is instructed
to disregard. C is more expressive but pays for a purpose axis that the retrieval
model already provides elsewhere.

---

## Strengths

**Candidate A (`engineering_decision`)**
- Already prescribed and enforced; zero further churn.
- Emphasizes that the object is organized *around* a decision.

**Candidate B (`decision_guide`)**
- Names the artifact — consistent with all sibling types and the `DG-` prefix.
- Extensible: future support artifacts each get a clean artifact noun
  (`checklist`, `threat_model`, `decision_tree`, `risk_model`,
  `reference_architecture`, `review_pack`), instead of collapsing into one
  purpose label.
- Aligns `type` with the retrieval model, the package guidance, and the EKB↔ECF
  boundary (EKB emits *support*, ECF makes *decisions*).
- Leaves `engineering_decision` free to mean an actual decision record later.

**Candidate C (two-axis)**
- Most expressive; makes purpose explicit and queryable.
- Cleanly separates identity from intent for tooling that needs both.

---

## Weaknesses

**Candidate A**
- Category error: types the object by its subject, not its identity.
- Does not scale to other decision-support artifacts — they would all be
  "engineering decisions," which is false and lossy.
- Contradicts every other reference to the object as a "Decision Guide."
- Blurs the EKB/ECF boundary by implying EKB stores decisions.

**Candidate B**
- Requires re-opening a decision just settled (a standards update + a second
  small migration).
- Minor: the sibling vocabulary is itself inconsistently prefixed
  (`engineering_concept` vs `example`); `decision_guide` matches the unprefixed
  group but not the prefixed one.

**Candidate C**
- Adds a second field (`purpose`/`intent`) that largely duplicates the retrieval
  model's intent mapping — redundant and a source of drift.
- Renaming the key (`type` → `artifact_type`) is itself a migration across *all*
  object types, not just DG-*, for marginal benefit.
- Premature: no current requirement needs a stored purpose axis (YAGNI).

---

## Long-term Impact

The decisive axis is **future extensibility**. The roadmap explicitly anticipates
Review Packs, Checklists, Threat Models, Decision Trees, Risk Models, Standards,
and Reference Architectures. Most of these are themselves **decision-support
artifacts**. Under purpose-typing (A), a Threat Model, a Decision Tree, and a
Decision Guide would all be `engineering_decision` — erasing exactly the
distinctions the ontology exists to preserve. Under artifact-typing (B/C), each is
a first-class noun.

Purpose-typing therefore accrues **conceptual debt** that compounds with every new
object family. Artifact-typing keeps `type` a stable identity axis and lets
purpose/intent remain a retrieval-time concern (where EKB already models it as
five engineering intents).

**Timing:** the graph currently holds **one** DG object and no ECF bundle has
pinned the type string. The blast radius of a correction today is: 1 knowledge
object, the engine's canonical constant, a handful of tests, and one standards
doc. After ECF adoption, every bundle and runner that matches the type string
multiplies that cost across repositories and requires coordinated cross-repo
migration. **The cost curve is lowest now and rises sharply after adoption.**

---

## Recommendation

Adopt **Candidate B — `type: decision_guide`** as the canonical value, framed by
the reasoning of **Candidate D**: `type` denotes *artifact identity*, and
`engineering_decision` is reserved (unused for now) for an actual decision
*record* should EKB ever store one.

Concretely (for a future, separately-authorized batch — **not** part of this
review):
1. Update `KNOWLEDGE_OBJECT_STANDARD.md` and `DECISION_GUIDE_STANDARD.md` to
   prescribe `decision_guide` as the artifact-identity type.
2. Establish the convention that the `type` vocabulary is artifact-noun-based, so
   future support artifacts get their own nouns.
3. Keep purpose/intent in the retrieval model, not on the object. Do **not** add a
   `purpose` field now (Candidate C) unless a concrete need appears.
4. Migrate the single DG object, the engine constant, and tests; regenerate the
   stale package.

Do **not** default to A merely because standards and code already encode it. The
standards are young, the object count is one, and the ontology is easier to get
right before ECF locks it in.

---

## Migration Impact

*(Impact analysis only — no migration is performed or authorized here.)*

- **In-repo (EKB):** small and mechanical — one DG object (`type` value), one
  engine constant (`DECISION` = `decision_guide`, with `engineering_decision`
  becoming the legacy alias, i.e. the inverse of the current mapping), the
  relevant tests, two standards docs, and regeneration of the gitignored package.
- **Cross-repo (ECF / bundles / Context Switcher):** none have consumed the type
  yet (they are parallel, unstarted, and out of this batch's ownership). If the
  correction is deferred until after ECF adoption, any bundle or runner matching
  `engineering_decision` must be refreshed — the expensive scenario.
- **Backward compatibility:** intentionally none at the string level (as with the
  first migration) — the previous value becomes the rejected legacy alias.
- **Net direction:** this would be a *second* correction reversing the value chosen
  by the first. It is not wasted work: the first migration achieved *consistency*
  (a real gain); this one would achieve *correctness* on top of that consistency.

---

## Confidence

**High** on the core finding: `engineering_decision` types the object by purpose,
not identity, and diverges from every sibling type and every other reference to
the object. The extensibility argument (future support artifacts) is decisive and
concrete.

**Medium-high** on the specific recommended value: `decision_guide` is clearly
better than `engineering_decision`; the only real contest is B vs the two-axis C,
and B wins on simplicity and non-duplication of intent — but a team that
genuinely needs a stored purpose axis could reasonably prefer C.

---

## Open Questions

1. **Naming convention:** should the whole vocabulary be uniformly prefixed
   (`engineering_decision_guide`, `engineering_example`) or uniformly unprefixed
   (`decision_guide`, `example`)? It is currently mixed. Pick one before adding
   more types.
2. **Will EKB ever store actual decision records (ADRs)?** If yes,
   `engineering_decision` should be reserved for those and kept distinct from
   `decision_guide`. If no, it can be dropped entirely.
3. **Does any consumer need purpose/intent as stored per-object metadata**, or is
   the retrieval model's intent mapping sufficient? This determines B vs C.
4. **Governance:** since this reverses a just-completed migration, who ratifies
   re-opening it, and should it be gated on the ECF-adoption timeline?

---

## Post-Review Questions

**Does the current ontology model the object or its purpose?**
Its **purpose**. `engineering_decision` names the decision the guide supports, not
the guide itself.

**Would you design this ontology differently if starting from scratch?**
Yes — artifact-identity typing (`type: decision_guide`) parallel to the sibling
types, with purpose/intent kept in the retrieval layer.

**Which representation minimizes future conceptual debt?**
`decision_guide` (artifact identity). Purpose-typing forces future
decision-support artifacts into a single wrong bucket, accruing debt with each new
family.

**Would changing now be cheaper than after ECF adoption?**
Decisively yes — one DG object and no ECF bundle consumes the type yet. Cost rises
sharply once bundles/runners pin the string across repos.

**Would you personally approve the migration?**
I would approve **re-opening** the type decision and standardizing on
`decision_guide`, *conditional on* updating the standards first and doing it
before ECF adoption. I would **not** approve it as a silent code change against
standards that still say `engineering_decision`, and I would not approve adding a
`purpose` field now. So: approve the corrected direction, via the proper
standards-first path — not an ad hoc migration.
