# ADR-0001: Use WinUI 3 as the Application Framework

**Status:** Accepted

**Date:** 2026-07-05

## Context

The project requires a modern, native Windows desktop application that provides a polished user experience, supports Fluent Design, and serves as a long-term foundation for an AI-assisted productivity application.

The chosen framework should:

* integrate well with modern Windows
* support rich UI and animations
* have long-term Microsoft support
* work well with C#
* support MVVM
* be appropriate for a single-developer project

## Decision

The project will use:

* C#
* .NET
* Windows App SDK
* WinUI 3

as the primary application framework.

## Alternatives Considered

### WPF

**Pros**

* Mature ecosystem
* Excellent documentation
* Large community
* Stable tooling

**Cons**

* Older UI framework
* Less aligned with Microsoft's forward-looking desktop strategy
* Requires more work to achieve a modern Fluent look

---

### .NET MAUI

**Pros**

* Cross-platform
* Shared code across operating systems

**Cons**

* Cross-platform support is not a project goal
* Additional complexity
* Less focus on delivering the best Windows experience

---

### Electron

**Pros**

* Large ecosystem
* Familiar web technologies

**Cons**

* Higher memory usage
* Less native Windows feel
* Unnecessary for a Windows-only product

---

### Avalonia

**Pros**

* Cross-platform
* Modern architecture

**Cons**

* Smaller ecosystem
* Windows-native experience is not as strong as WinUI 3
* Cross-platform support is not currently required

## Consequences

### Positive

* Modern Fluent Design support
* Native Windows experience
* Good integration with Windows App SDK
* Strong foundation for future UI enhancements
* Supports our long-term product vision

### Negative

* Smaller ecosystem than WPF
* Some APIs and tooling continue to evolve
* Learning curve for WinUI-specific patterns

## Assumptions

* Windows remains the primary platform.
* The application is intended for long-term use.
* Rich Windows-native UX is more valuable than cross-platform compatibility.

## Review Trigger

Revisit this decision if:

* Cross-platform support becomes a strategic goal.
* Microsoft significantly changes its desktop UI direction.
* WinUI 3 no longer meets performance or maintenance needs.

## Approval

Approved by: Project Owner

Date: 2026-07-05
