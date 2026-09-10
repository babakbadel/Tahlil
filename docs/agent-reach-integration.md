# Agent Reach → BabiMind / Tahlil

## Upstream

BabiMind uses **Panniantong/Agent-Reach** as an external research/access layer. The upstream repository is pinned in `config/agent_reach.yml` so a change in upstream behavior does not silently change historical runs.

Agent Reach provides access paths for web pages, web search, YouTube, RSS, GitHub, Twitter/X, Reddit and other platforms, with platform-specific fallback backends and a `doctor` health check.

## Position in BabiMind

```text
Agent Reach
    ↓
External Research / Sentiment
    ↓
Raw provenance + timestamp
    ↓
Validation / source confidence
    ↓
BabiMind factors
    ↓
Cross-check with TSETMC / Codal / official sources
    ↓
Scenario + Decision Engine
```

Agent Reach is **not** a replacement for primary financial data. It is a discovery, web-reading and sentiment/research layer. Official market and company sources retain higher priority.

## Tahlil files

- `config/agent_reach.yml` — pinned upstream revision, policy and channel map.
- `scripts/collect_agent_reach.py` — fail-open health/provenance collector.
- `artifacts/agent_reach/` — machine-readable health snapshots.
- `.github/workflows/babimind-research.yml` — installs the pinned revision and runs the health collector as part of research.

## Market applications

Agent Reach can enrich BabiMind research around:

- FMLI / copper / metals and sector rotation
- ZOB and steel sentiment
- banks and automotive sentiment
- oil/refining and global commodities
- options/news context
- dollar and gold narratives
- macro and geopolitical event discovery

These signals must be timestamped and cross-validated. Missing Agent Reach data is **not zero** and does not invalidate the rest of the pipeline.

## Update policy

1. Inspect upstream changes.
2. Change the pinned commit in `config/agent_reach.yml` and workflow environment together.
3. Run the health check.
4. Compare source coverage and outputs against the previous revision.
5. Only then promote the new revision for regular BabiMind research.
