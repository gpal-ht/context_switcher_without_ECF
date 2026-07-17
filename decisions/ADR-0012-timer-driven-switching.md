# ADR-0012: Timer-Driven Switching

**Status:** Accepted

**Date:** 2026-07-17

**Approved by:** Project Owner (directive: "build the next slice:
timer-driven switching", 2026-07-17)

**Related Work:** ADR-0008 (Work Engine), ADR-0009 (Work Session Lifecycle),
ADR-0011 (WinUI 3 GUI Shell); `docs/features/project_context_switch.md`
(open question 1: "Should context switching be timer-driven, manual, or
both?"); `docs/architecture/WORK_SESSION_MODEL.md`; README Phase 1
("Focus timer").

## Context

Manual context switching works today (start → end/wrap-up → switch →
resume). The roadmap's Phase 1 "Focus timer" and the feature doc's flow
("Timer or manual switch triggers a transition") call for a **timer-driven**
path: begin a focused work session with a planned duration, and when that
time elapses, be prompted to wrap up and switch. This answers the feature
doc's open question with **both** — manual remains; timing is additive.

CLAUDE.md safety rules bound the interruptive behavior: the app must not
behave like malware, must not block Task Manager / Alt-Tab / Ctrl-Alt-Del,
must not prevent exit, and **interruptive UI must always include a safe
escape path**. The timer prompt is therefore a non-blocking, dismissable
nudge — never a forced modal, never always-on-top, never auto-switching
without consent.

## Decision

### Timing is a domain concept; ticking is a UI concern

- A work session gains an **optional planned duration**
  (`WorkSession.PlannedDuration`, `TimeSpan?`). Absent → an untimed session
  (today's behavior, unchanged).
- The domain computes timing **purely** from the session and an injected
  "now": `Deadline`, `RemainingAt(now)`, `IsElapsedAt(now)`. No wall-clock
  reads inside the domain — fully deterministic and unit-testable (the
  ADR-0008 clock-injection pattern).
- The **UI owns the tick**: the GUI runs a `DispatcherTimer` (1 s) that
  recomputes the countdown from the open session + `DateTimeOffset.UtcNow`.
  The domain never spawns threads or timers.

### Service surface

- `StartSession(objective, plannedDuration?)` — validates the duration
  (must be > 0 and ≤ 24 h; otherwise `ValidationException`).
- `ExtendActiveSession(by)` — "snooze": moves the deadline to `now + by`
  (elapsed-so-far + `by`), so an already-elapsed timer gets a fresh window.
  Requires an open session.
- No new persistence mechanism: `PlannedDuration` is an **additive** field
  on the persisted session. Per ADR-0009, additive optional fields do not
  bump the schema version — a pre-timer `0.1.0` workspace loads with
  `PlannedDuration = null`.

### Interruptive prompt (GUI) — a safe nudge

When the active session is open and elapsed, the shell shows a **non-modal
`InfoBar`** (Warning severity): "Focus time is up — wrap up and switch?"
with:
- **Wrap up now** — reveals/focuses the end-session form (does not force it);
- **Extend 5 min** — calls `ExtendActiveSession(5 min)`;
- the InfoBar's built-in **close (X)** — dismiss/postpone.

No action is forced; closing the app, ignoring the bar, or continuing work
are all allowed. The window stays an ordinary, closable desktop window.

### CLI parity

`session start` accepts `--minutes <n>`; `status` shows remaining time
("12m left") or an elapsed notice ("focus time is up") so the timed flow is
scriptable and deterministically checkable without the GUI.

## Consequences

- Sessions can be timed; the GUI counts down live and nudges at elapse; the
  CLI reports remaining/elapsed. Untimed sessions behave exactly as before.
- Timing logic is unit-tested via injected clocks; the GUI tick and prompt
  are presentation over that tested core.
- No background service, tray, OS notification, or auto-switch in this slice
  — those are later slices. The nudge is in-window only, honoring the safety
  rules.
- Persistence stays backward-compatible (additive, schema unchanged).

## Non-goals (this slice)

OS-level notifications / toasts, system tray, sound/alerts, auto-start of the
next session, background operation while the window is closed, and
configurable default durations. Deliberately out to keep the slice reviewable
and the interruptive surface minimal and safe.
