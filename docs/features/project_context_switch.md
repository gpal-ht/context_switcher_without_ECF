# Feature: Project-to-Project Context Switch

## Status

Draft

## Purpose

Help the user intentionally end work on one project and begin work on another with minimal loss of context.

## User Problem

When switching projects, the user loses track of:

- what was just completed
- what remains unfinished
- what decisions were made
- what should be remembered later
- what to work on next

## User Flow

1. User is working on Project A.
2. Timer or manual switch triggers a transition.
3. App asks the user to wrap up Project A.
4. User records:
   - completed work
   - unfinished work
   - blockers
   - notes for future self
5. User selects Project B.
6. App shows Project B resume context.
7. User starts the next work session.

## MVP Requirements

The MVP should support:

- a list of projects
- an active project
- a current work session
- manual context switch
- wrap-up form
- next project selection
- session history

## Out of Scope for MVP

- AI-generated recommendations
- calendar integration
- automatic app/window detection
- cloud sync
- team collaboration
- full workday automation

## Required Data

### Project

- id
- name
- description
- status
- created date
- updated date

### Work Session

- id
- project id
- start time
- end time
- duration
- wrap-up entry

### Wrap-Up Entry

- completed work
- unfinished work
- blockers
- future-self notes
- next action

## UX Principles

- The switch flow should feel calm, not punitive.
- The wrap-up form should be short enough to complete quickly.
- The user should be able to escape or postpone.
- The app should encourage reflection without becoming annoying.

## Risks

- The form may feel like friction.
- The app may interrupt at a bad time.
- Too much structure may reduce adoption.
- Too little structure may fail to preserve useful context.

## Open Questions

1. Should context switching be timer-driven, manual, or both?
2. What fields are truly required in the wrap-up form?
3. Should the next project always be selected immediately?
4. Should incomplete wrap-ups be allowed?
5. How should emergency escape behave?

## Implementation Status

Implementation in progress (approved by the project owner, 2026-07-16;
conventions per ADR-0008; work-session lifecycle per ADR-0009).

| MVP requirement | Status |
| --- | --- |
| A list of projects | **Implemented** — Work Engine project registry (`src/Work/ContextSwitcher.Work`) with create/list/archive, local JSON persistence, interim CLI harness |
| An active project | **Implemented** — active-project selection with archived-project guard |
| A current work session | **Implemented** — `WorkSessionService` start/end on the active project; one open session at a time (`session start` / `session end` / `status`) |
| Manual context switch | **Implemented (core loop)** — end (wrap up) → `project switch` → `resume` → start again; timer/auto-switch is a later slice |
| Wrap-up form | **Implemented** — required outcome + optional completed/unfinished/blockers/future-self-notes/next-action (`session end`) |
| Next project selection | **Implemented** — `project switch` followed by `resume` shows the target project's last wrap-up |
| Session history | **Implemented** — `session list` for the active project, most recent first |

Remaining for this feature: per-project history for non-active projects,
timer-driven / automatic switching, and AI-assisted wrap-up drafts (MVP
non-goals or later requirements).