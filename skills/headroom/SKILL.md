# Headroom Skill

Use the official Headroom context-optimization workflow when this repository is used with an MCP-compatible coding agent.

## Capabilities
- Compress large tool outputs, logs, files, RAG chunks and other context before reasoning.
- Use reversible compression/retrieval when originals may be needed.
- Track compression/retrieval statistics.
- Preserve critical project instructions and evidence; do not blindly compress canonical instructions or source-of-truth records.
- Prefer `headroom_compress` for large content and `headroom_retrieve` only when the retained summary is insufficient.

## MCP
Official package: `headroom-ai[mcp]`.
MCP server command: `headroom mcp serve`.

## Tahlil integration
Headroom is a context-optimization layer only. It must not replace the Tahlil Knowledge Graph, evidence records, Decision History, or historical `as_of` snapshots.

## Official source
https://github.com/headroomlabs-ai/headroom
