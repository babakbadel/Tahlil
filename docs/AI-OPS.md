# AI Operations: Graphy + Headroom + Logging

This repository follows the project-wide AI operating rules.

## Graphy
- Model important project entities, dependencies, decisions, APIs, data flows, and relationships as a connected graph.
- Prefer graph-aware reasoning over isolated module decisions.
- When changing architecture, update the relevant graph/documentation nodes and relationships.

## Headroom
- Keep prompts, context, tool output, and generated artifacts compact and structured.
- Preserve critical project state while avoiding redundant context.
- Prefer incremental changes, explicit checkpoints, and concise status summaries.

## Logging
- Record significant development actions, deployments, tests, errors, and architectural decisions.
- Keep secrets, tokens, credentials, and personal data out of logs.
- Use structured logs where the application supports them.
- Keep a project decision/history trail in Git commits, PRs, issues, and project documentation.

These rules are operational guidance and do not replace application-specific security or logging requirements.
