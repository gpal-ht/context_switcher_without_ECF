# Bundle Rules

## Purpose

Context Switcher consumes ECF as a versioned engineering dependency.

## Core Rule

Files inside `vendor/` are read-only.

Do not modify bundled ECF files from this repository.

## Include

When bundling ECF into Context Switcher, include:

- README.md
- FOUNDATION.md
- FRAMEWORK_ARCHITECTURE.md
- ECF_ROADMAP.md
- knowledge/
- standards/
- transformations/
- roles/
- review_packs/
- workflows/
- quality_gates/
- execution/
- vendor/engineering_kb/

## Exclude

Do not bundle:

- .git/
- generated/
- runtime/
- cache/
- logs/
- temporary files
- local IDE settings

## Guiding Principle

Context Switcher adopts ECF.

It does not redefine ECF.