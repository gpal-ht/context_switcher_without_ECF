# ADR-0017: Estimation Accuracy Trends

**Status:** Accepted

**Date:** 2026-07-17

**Approved by:** Project Owner (directive: "build the next slice: estimation
accuracy trends", 2026-07-17)

**Related Work:** ADR-0012 (planned durations), ADR-0013 (Overrun), ADR-0015
(Focus Trends Insights — first estimation figures), ADR-0016 (recurring
blockers); `docs/architecture/DOMAIN_MODEL.md` ("Insight" — estimation
accuracy); README Phase 4.

## Context

ADR-0015 surfaced coarse estimation figures (how many timed sessions ran over,
average overrun). It answers "did I run over?" but not "how accurate are my
estimates, and am I getting better?" — the DOMAIN_MODEL's "estimation
accuracy" Insight. This slice adds a proper **accuracy metric**, an
**over/under bias**, and a **directional trend** (recent vs earlier), from the
planned-vs-actual data already recorded on timed sessions.

## Decision

### Per-session accuracy (domain)

Add `WorkSession.EstimationAccuracy` (double 0..1) — for a **closed, timed**
session, `max(0, 1 - |actual - planned| / planned)`: 1.0 is a perfect
estimate, 0 means off by 100% or more. Null for untimed or open sessions.
Pure derived property (like `Overrun`), unit-tested.

### An estimation-trend summary (service)

Add `EstimationBias` (`UnderEstimates` | `OverEstimates` | `WellCalibrated`)
and `EstimationTrend` (scope, timed count, `AverageAccuracyPercent`,
`AverageError` signed = actual − planned, `Bias`, and the recent-vs-earlier
`RecentAccuracyPercent` / `EarlierAccuracyPercent` + `Improving`).

`WorkSessionService.ComputeEstimationTrend(projectNameOrId = null)`:
- over closed **timed** sessions for a scope (one project via the shared
  `ProjectLookup`, or all projects);
- `AverageAccuracyPercent` = mean per-session accuracy × 100;
- **Bias** from the mean signed error relative to the mean plan (within ±10%
  is `WellCalibrated`; a positive error — running over — is `UnderEstimates`;
  negative is `OverEstimates`);
- **Trend**: order the timed sessions oldest→newest, split into an earlier and
  a recent half (the recent half takes the extra when odd), and compare their
  average accuracy — `Improving` is true when recent beats earlier. Requires
  at least two timed sessions; otherwise the trend fields are null.

Pure over the stored sessions (no clock needed); reads state, writes nothing.

### Surfaces

- **CLI:** `estimation [--project <name|id>]` — accuracy %, bias, and trend.
- **GUI:** a read-only **Estimation accuracy** panel (workspace scope),
  recomputed on refresh.

## Consequences

- Users see how well-calibrated their time estimates are and whether they are
  improving — actionable feedback that rewards setting focus timers.
- Builds on existing data; no persistence, schema, or migration impact.
- The coarse ADR-0015 estimation line stays (a quick "ran over" count); this
  slice adds the accuracy metric and trend alongside it.

## Non-goals (this slice)

Per-project-type calibration, confidence intervals, charts, configurable
tolerance/windows, and predictive suggestions ("this usually takes you 40m")
— later slices. This establishes the accuracy metric, bias, and a first
directional trend.
