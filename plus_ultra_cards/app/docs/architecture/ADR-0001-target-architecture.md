# ADR-0001: Target Architecture for Plus Ultra Cards

Date: 2025-09-01
Status: Proposed

## Context
Fixes to text rendering (cloze, style markup) often cascade into UI and study behavior. CardManager mixes multiple responsibilities. Lack of plugin points for card types/SRS engines makes extension and testing difficult.

## Decision
Adopt a layered architecture with clear boundaries and interfaces:

- presentation (Qt views) -> controllers/adapters -> domain/services -> infrastructure
- formatting is a pure service with a deterministic pipeline
- card types and SRS engines are plugins behind interfaces

## Consequences
- Reduced coupling: UI will depend on interfaces
- Deterministic rendering pipeline avoids HTML-escaping issues
- Easier addition of new card types/SRS engines

## Details
- Introduce interfaces and facades without moving files initially
- Later reorganize modules into domain/, formatting/, presentation/, infrastructure/
- Establish typed error categories and structured logging

## Alternatives considered
- Incremental fixes only: rejected due to ongoing regressions
- Full rewrite: too risky and time-consuming

## Rollout
- Phase 0–2: Contracts + facades + controller skeleton under feature flag
- Phase 3+: Module moves and removing shims

