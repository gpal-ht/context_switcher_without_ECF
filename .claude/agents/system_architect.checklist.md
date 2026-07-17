# System Architect Review Checklist

Use this checklist before any implementation begins.

## Architectural Fit

* [ ] Which subsystem owns this feature?
* [ ] Are responsibilities clear?
* [ ] Does the feature respect subsystem boundaries?
* [ ] Is there a simpler design?

## Domain Impact

* [ ] Does it introduce a new domain concept?
* [ ] Does it modify an existing concept?
* [ ] Does it affect the Knowledge Architecture?
* [ ] Does it affect the Runtime Model?

## Dependency Review

* [ ] New dependency introduced?
* [ ] Existing dependency modified?
* [ ] Any circular dependency risk?
* [ ] Can the feature be implemented independently?

## ADR Review

* [ ] Does this require a new ADR?
* [ ] Does it invalidate an existing ADR?
* [ ] Does it change an architectural principle?

## Event Review

* [ ] Are new Commands required?
* [ ] Are new Events required?
* [ ] Are event names meaningful?
* [ ] Is event ownership clear?

## Complexity Review

* [ ] Can this be delivered incrementally?
* [ ] Is any abstraction premature?
* [ ] Does the design increase accidental complexity?
* [ ] Will this still make sense one year from now?

## Review Result

Choose one:

* Approve
* Approve with recommendations
* Needs redesign
* Block

Provide a concise rationale for the decision.
