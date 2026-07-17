# REVIEW_PACKS.md

# Purpose

Review Packs define the standard combinations of specialist reviewers that should participate in different engineering activities.

Rather than manually selecting reviewers for every feature, the appropriate Review Pack should be used.

This ensures consistent engineering quality while avoiding unnecessary reviews.

---

# General Rules

* Use the smallest Review Pack that provides sufficient confidence.
* Do not invoke specialists whose expertise is not relevant.
* Every review produces artifacts.
* Human approval is always required before implementation.

---

# Review Pack: New Feature

## Use When

A new user-facing capability is proposed.

## Specialists

* Product Architect
* System Architect
* Knowledge Architect
* Runtime Architect
* Test Architect

## Required Outputs

* Product Review
* Architecture Review
* Knowledge Impact Assessment
* Runtime Impact Assessment
* Test Strategy

---

# Review Pack: AI Feature

## Use When

The feature uses AI or modifies AI behavior.

Examples:

* AI recommendations
* AI summaries
* Prompt changes
* ChatGPT imports
* Repository evaluation
* Semantic search

## Specialists

* Product Architect
* System Architect
* Knowledge Architect
* AI Architect
* Security Architect
* Test Architect

## Required Outputs

* Product Review
* Architecture Review
* Knowledge Impact Assessment
* AI Impact Assessment
* Security Assessment
* Test Strategy

---

# Review Pack: User Interface

## Use When

The feature primarily changes user interaction.

Examples:

* New screens
* Dialogs
* Forms
* Navigation
* Notifications
* Overlay experience

## Specialists

* Product Architect
* Accessibility Architect
* Runtime Architect
* Test Architect

## Required Outputs

* Product Review
* Accessibility Assessment
* Runtime Impact Assessment
* Test Strategy

---

# Review Pack: Integration

## Use When

The feature connects to external systems.

Examples:

* Git repositories
* ChatGPT exports
* Future calendar integration
* File import/export

## Specialists

* Product Architect
* System Architect
* Security Architect
* AI Architect (if applicable)
* Test Architect

## Required Outputs

* Product Review
* Architecture Review
* Security Assessment
* AI Impact Assessment (if applicable)
* Test Strategy

---

# Review Pack: Architecture Change

## Use When

A proposal changes the system architecture.

Examples:

* New subsystem
* New domain concept
* Major dependency
* Storage strategy
* Event model
* Runtime model

## Specialists

* System Architect
* Knowledge Architect
* Runtime Architect
* ADR Guardian
* Repository Guardian

## Required Outputs

* Architecture Review
* Knowledge Impact Assessment
* Runtime Impact Assessment
* ADR Compliance Report
* Repository Health Report

Implementation must not begin until the ADR is approved.

---

# Review Pack: Documentation

## Use When

Adding or modifying engineering documentation.

## Specialists

* Documentation Guardian
* Repository Guardian

## Required Outputs

* Documentation Review
* Repository Health Report

---

# Review Pack: Bug Fix

## Use When

Fixing an existing defect without changing architecture.

## Specialists

* System Architect
* Test Architect

## Required Outputs

* Architecture Review
* Test Strategy

If the bug reveals an architectural weakness, escalate to the Architecture Change Review Pack.

---

# Escalation Rules

Escalate to a larger Review Pack when:

* a new domain concept is introduced
* an ADR is required
* security or privacy is affected
* AI is introduced into an existing workflow
* recoverable runtime state changes
* external integrations are added

---

# Human Approval

Review Packs produce recommendations.

They do not authorize implementation.

Only the Project Owner may approve implementation.

---

# Guiding Principle

Review Packs exist to increase engineering confidence through focused, repeatable, and proportionate review.

The goal is not to maximize process.

The goal is to maximize decision quality while keeping development efficient.
