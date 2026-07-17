# Runtime Model

## Purpose

This document defines the runtime behavior of Context Switcher.

It describes the information required while the application is executing and how that information is managed, recovered, and synchronized with the Knowledge Architecture.

Unlike Knowledge, Runtime State exists to support active workflows and user interactions.

---

# Core Principle

The application distinguishes three categories of information:

1. Persistent Knowledge
2. Recoverable Runtime State
3. Transient UI State

Each category has different lifecycle and recovery requirements.

---

# Persistent Knowledge

Persistent Knowledge is the system of record.

Examples:

* Projects
* Knowledge Items
* Context Snapshots
* Resume Briefs
* Session History

Knowledge should never depend on runtime state.

---

# Recoverable Runtime State

Recoverable Runtime State represents ongoing work.

Loss of this information would negatively affect the user experience.

Examples:

* Active Work Session
* Session Objective
* Current Timer
* Active Project
* Draft Wrap-Up
* Pending Context Switch
* Repository Scan
* AI Analysis in Progress

Recoverable Runtime State should survive unexpected application termination whenever practical.

---

# Transient UI State

Transient UI State exists only to support presentation.

Examples:

* Selected navigation item
* Window layout
* Expanded panels
* Scroll position
* Current dialog
* Animation progress

Loss of UI state should never affect user knowledge.

---

# Runtime Recovery

The application should recover gracefully after an unexpected shutdown.

On startup, the application should detect recoverable runtime state and present the user with recovery options.

Examples:

* Resume interrupted work session
* Continue context switch
* Restore draft wrap-up
* Restart repository analysis
* Discard recovered state

Recovery should always be initiated by the user.

---

# Session Checkpoints

Long-running activities should create periodic checkpoints.

Examples:

* Work Session started
* Timer resumed
* Draft updated
* Context switch initiated
* AI request submitted
* Repository analysis completed

Checkpoints should contain only the minimum information required to resume the activity.

---

# Runtime Events

The application should be event-driven.

Examples:

* Work Session Started
* Timer Paused
* Knowledge Item Created
* Context Switch Requested
* Wrap-Up Completed
* Repository Scan Finished
* AI Recommendation Approved

Events update Runtime State and may result in changes to Persistent Knowledge after user confirmation.

---

# Synchronization

Runtime State and Knowledge interact continuously.

Typical flow:

Knowledge
↓
Initialize Runtime
↓
User Works
↓
Runtime Checkpoints
↓
Session Outcome
↓
Knowledge Updated

Knowledge remains the long-term source of truth.

Runtime exists to support the user's current activity.

---

# Design Principles

The Runtime Model should:

* recover gracefully
* minimize data loss
* preserve user trust
* remain understandable
* support long-running workflows
* isolate presentation concerns
* avoid unnecessary persistence

---

# Success Criteria

The Runtime Model is successful when:

* application crashes rarely result in lost work
* runtime workflows are recoverable
* knowledge remains consistent
* recovery is predictable
* users remain in control of recovery decisions
