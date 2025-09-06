Plus Ultra Cards — Architecture Refactor Plan (Phase 0–2)
=======================================================

Purpose
- Reduce tight coupling between UI, rendering, and study logic
- Provide plugin points for card types and SRS engines
- Make rendering pipeline deterministic and testable
- Improve error transparency and developer velocity

Scope of this plan
- Planning and scaffolding only (no behavior changes, no file moves)
- Add documentation, interfaces, and facades in existing folders
- Prepare tests for key contracts

Current pain points (summary)
- UI contains card-type logic and rendering policy (StudyWindow, CardEditor)
- CardManager mixes repository and SRS orchestration
- Rendering order/escaping unclear; cloze and style markup interact unpredictably
- Weak plugin story for card types and SRS engines

Guiding principles
- Clear boundaries: presentation ⇢ controller ⇢ domain/services ⇢ infra
- Dependency inversion: UI depends on interfaces, not implementations
- Deterministic, staged rendering pipeline
- Typed errors, structured logging

Deliverables in Phase 0–2
- ADR-0001 Target Architecture (docs/architecture)
- Interfaces/Facades (non-invasive):
  * app/srs/interfaces.py — SrsEngine protocol
  * app/formatting/formatter_service.py — Facade around TextFormatter
  * app/core/card_types.py — CardType interface + registry + basic/cloze adapters
  * app/core/study_controller.py — Headless controller skeleton (not wired to UI)
- Tests:
  * tests/test_formatter_service_facade.py (facade behavior)

Phases

Phase 0 — Baseline & Contracts (this PR)
- Add plan/ADR docs
- Add protocols/facades and minimal tests
- No changes to existing behavior or imports elsewhere

Phase 1 — Route through facades (no file moves)
- StudyWindow and CardEditor call FormatterService instead of TextFormatter directly
- StudyWindow uses CardTypeRegistry to decide single‑ vs dual‑sided but keeps existing logic
- CardManager keeps API; introduce CardService (internal) without moving files

Phase 2 — Introduce StudyController and feature flag
- Wire StudyWindow to StudyController behind a feature flag
- Controller emits state/viewmodel; UI becomes passive view
- SRS usage behind SrsEngine interface; dt_adapter implements it

Success criteria
- Rendering bugs isolated to formatting layer; UI changes don’t affect behavior
- Adding a new card type or SRS engine requires no UI changes
- Errors include source layer (formatting/study/srs/repo) and identifiers (card_id, session_id)

Risks & mitigations
- Hidden side effects: add golden tests for rendering and flip/reveal flow
- Refactor churn: maintain compatibility shims until Phase 3 (future)

Next steps after Phase 2 (future work)
- Module reorganization into domain/, formatting/, presentation/, infrastructure/
- Remove shims and eliminate direct DB access from services
- CI: linting, typing, coverage gates

