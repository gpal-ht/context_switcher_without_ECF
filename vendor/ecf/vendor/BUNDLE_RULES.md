# Bundle Rules

## Purpose

Vendor bundles allow one repository to consume a versioned copy of another repository without relying on sibling folders, chat history, or AI memory.

## Core Rule

Bundled dependencies are read-only.

Do not modify files inside `vendor/` directly.

Changes must be made in the source repository, committed there, and then re-bundled.

## ECF Dependency

ECF may bundle:

```text
engineering_kb