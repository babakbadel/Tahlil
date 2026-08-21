# Graphify Skill — Tahlil

Graphify-style knowledge graph workflow for the Tahlil project.

## Mandatory rules
- Extract entities and relationships from project documents, decisions, evidence, people, events, market data and code.
- Mark every relationship `EXTRACTED` or `INFERRED`.
- `INFERRED` relationships must never be presented as directly sourced facts.
- Preserve `source`, `source_published_at`, `observed_at`, `valid_from`, `valid_to`, and confidence where applicable.
- Maintain historical snapshots so the graph can be reconstructed with `as_of` timestamps.
- Prevent look-ahead bias in all historical analysis.

## Core Tahlil graph
`Person -> Role -> Institution -> Event -> Decision -> Economic Impact -> Market -> Security`

## Decision integration
Graph context is an input to the `تصمیم` engine and its Decision History. Every prediction should be traceable to the graph snapshot and evidence available at prediction time.

## People network
The graph must support the Pezeshkian government influence network under `people/` and connect people, roles, relationships, events, evidence and decisions.
