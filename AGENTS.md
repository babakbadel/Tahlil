# Tahlil Engineering Rules

## Scope
These rules apply to all AI/Codex-assisted work in Tahlil.

## Project Role
Tahlil is an analysis/research system. Preserve evidence, provenance, chronology and reproducibility. Do not silently convert assumptions into facts.

## Core Architecture
Analysis, Graphy, game theory, dynamic systems, economic variables and decision history should be modeled as connected analytical layers, not isolated notes.

## Workflow
ANALYZE -> EVIDENCE -> MODEL -> IMPLEMENT -> TEST -> VERIFY -> LOG.
Separate observed data, derived metrics, hypotheses and predictions.

## Graphy
Use the `graph/` area as the project's relationship/impact graph. Track entities, relationships, dependencies, critical nodes, propagation and uncertainty. When an analysis changes, inspect its graph impact.

## Headroom
Review model complexity, data quality, source coverage, computational cost, storage, maintainability and uncertainty headroom before adding complexity. Prefer measurable limits over invented thresholds.

## Skills
Existing skills under `skills/` are project-specific knowledge. New reusable agent workflows should live under `.agents/skills/` when appropriate.

## Memory and Chats
Preserve useful historical context in `memory/` and `chats/` without exposing secrets or personal credentials. Historical records should not be rewritten merely to fit a new hypothesis.

## Logging
Important changes belong in `docs/logs/`. Record timestamp, objective, evidence/context, changed areas, Graphy impact, Headroom impact, verification, result and next step.

## Decisions
Record important model/architecture decisions in `docs/decisions/` with rationale, alternatives and consequences.

## Integrity
Never fabricate sources, measurements, tests, deployments or certainty. When external information may have changed, verify it from an appropriate current source.
