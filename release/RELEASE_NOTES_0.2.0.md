# Context Switcher — Release Notes 0.2.0 (historical)

Package: `@gpal-ht/context-switcher`
Version: `0.2.0`
Private: `true` — not published to any registry.

> **Historical note (ADR-0010).** The `0.2.0` line was the ECF-consumer
> *release-engineering foundation* inherited from the parent `context_switcher`
> repository — its content was ECF/EKB adoption, bundling, and offline consumer
> verification. This repository forked that foundation into a **standalone
> application** and removed ECF entirely
> ([ADR-0010](../decisions/ADR-0010-remove-ecf-integration.md)). The details
> below are retained only as lineage; they do not describe this repository's
> current release content.

## What this repository actually contains now

- A standalone .NET Work Engine: project registry (ADR-0008) and work-session
  lifecycle with wrap-up (ADR-0009), with local JSON persistence and an interim
  CLI harness.
- No bundled framework, no network dependency, a single operating mode.
- An app-only offline release harness (manifest + validator) and acceptance
  suite.

## Superseded 0.2.0 lineage (parent repository)

The original 0.2.0 foundation bundled ECF under `vendor/ecf/`, shipped consumer
wrapper scripts, governed work via a Work Request catalog, and verified an
offline ECF pipeline. All of that was removed here by ADR-0010. The next
release notes for this repository will be app-scoped and carry a new version.
