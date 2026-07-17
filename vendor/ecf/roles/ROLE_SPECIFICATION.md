# ROLE_SPECIFICATION.md

# Purpose

This specification defines the structure, responsibilities, authority, and lifecycle of Roles within the Engineering Control Framework (ECF).

A Role represents an engineering responsibility.

A Role is independent of who or what performs it.

---

# Core Principle

ECF defines responsibilities, not executors.

A Role may be fulfilled by:

- a human
- an AI assistant
- an automated tool
- a team
- a hybrid human-AI process

---

# What Is a Role?

A Role is a named engineering responsibility within ECF.

Examples:

- Product Architect
- System Architect
- Security Architect
- Accessibility Architect
- Test Architect
- Delivery Architect
- Repository Guardian

Roles may perform:

- Knowledge Transformations
- Reviews
- Quality Gate evaluations
- Artifact production
- Artifact validation

---

# Required Role Structure

Every Role definition must include:

## Identity

- Role ID
- Name
- Version
- Status
- Category

## Mission

The purpose of the Role.

## Responsibilities

The engineering concerns owned by the Role.

## Authority

What the Role may approve, reject, block, or escalate.

## Inputs

Artifacts, standards, workflows, or context required by the Role.

## Outputs

Artifacts, reviews, assessments, or recommendations produced by the Role.

## Review Questions

Questions the Role must answer when participating in a review.

## Blocking Conditions

Conditions under which the Role may block progress.

## Success Criteria

How to judge whether the Role performed effectively.

---

# Role Categories

## Architecture Roles

Examples:

- Product Architect
- System Architect
- Knowledge Architect
- Runtime Architect
- Delivery Architect

## Quality Roles

Examples:

- Security Architect
- Accessibility Architect
- Test Architect
- Performance Architect
- AI Architect

## Governance Roles

Examples:

- Repository Guardian
- ADR Guardian
- Documentation Guardian

---

# Role Authority

Roles may have different authority levels.

## Advisory

May provide recommendations.

## Required Reviewer

Must review before work may proceed.

## Blocking Reviewer

May block progress until concerns are resolved.

## Approver

May approve a Quality Gate when authorized.

Human approval remains the final authority unless a project explicitly defines otherwise.

---

# Executor Independence

A Role definition must not depend on a specific tool or AI provider.

Incorrect:

- Claude reviews security.

Correct:

- Security Architect reviews security.
- Claude may execute the Security Architect Role.

---

# Role Lifecycle

Draft

↓

Reviewed

↓

Approved

↓

Adopted

↓

Revised

↓

Deprecated

↓

Archived

---

# Relationship to Review Packs

Review Packs select Roles required for a type of work.

Example:

AI Feature Review Pack may require:

- Product Architect
- System Architect
- Knowledge Architect
- AI Architect
- Security Architect
- Test Architect

---

# Relationship to Knowledge Transformations

Knowledge Transformations may specify Roles responsible for:

- producing artifacts
- reviewing outputs
- approving progression
- resolving findings

---

# Guiding Principle

A Role exists because a responsibility must be owned.

If no distinct engineering responsibility exists, no Role should be created.