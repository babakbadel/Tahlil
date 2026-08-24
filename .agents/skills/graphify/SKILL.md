---
name: graphify
description: "Use Graphify as the knowledge-graph and relationship layer for BabiMind/Tahlil. Preserve source memory in full; use Graphify for entity/relationship indexing, traversal, fast retrieval, and codebase/project queries."
---

# Graphify — BabiMind Knowledge Graph Layer

Graphify is the graph/index layer beside BabiMind memory. **Do not summarize or replace source memory.** Keep original chats, reports, market data, decisions, and documents intact; use Graphify to index entities and relationships so BabiMind can retrieve relevant memory quickly.

## Official implementation

- Repository: https://github.com/Graphify-Labs/graphify
- Package: `graphifyy`
- Install/update: `uv tool install --upgrade graphifyy` (or `python3 -m pip install --upgrade graphifyy`)
- CLI: `graphify`

## Core commands

```bash
graphify .
graphify <path>
graphify <path> --update
graphify <path> --mode deep
graphify query "<question>"
graphify query "<question>" --budget 1500
graphify path "<node1>" "<node2>"
graphify explain "<node>"
graphify <path> --mcp
```

## BabiMind rules

1. **Memory is the source of truth.** Never delete or replace original information because a graph was created.
2. **Graphify is an index/relationship layer.** Store nodes, edges, provenance, timestamps, and relationship type (`EXTRACTED`, `INFERRED`, `AMBIGUOUS`) where supported.
3. For BabiMind analysis, query Graphify first when the question concerns relationships, project architecture, prior decisions, actors, market concepts, or connected evidence.
4. After graph retrieval, fetch the underlying full memory/source records needed for the actual analysis.
5. Do not treat inferred edges as facts; preserve provenance and confidence.
6. Prefer incremental updates (`--update`) after new/changed project content.
7. Keep `graphify-out/` as generated graph output; do not put raw memory there unless explicitly intended.

## BabiMind conceptual graph

```text
Full Memory (unchanged)
        |
        +---- Graphify Index
                 |
           Nodes + Edges
                 |
          Relationship Search
                 |
          Relevant Memory IDs
                 |
              BabiMind
```

## First-run behavior

If the `graphify` executable is unavailable, install `graphifyy` using the official package instructions above, then run Graphify. Do not request an Anthropic/OpenAI API key merely to graph code; Graphify can structurally process code without one. For semantic extraction, use only credentials already configured by the host environment.
