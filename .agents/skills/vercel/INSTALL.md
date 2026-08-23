# Vercel Agent Skills

This project uses the official Vercel Agent Skills collection:

- Source: `vercel-labs/agent-skills`
- CLI: `npx skills`
- Official install command: `npx skills add vercel-labs/agent-skills --all`

## Supported agents

For Codex/project agents, install into the project with:

```bash
npx skills add vercel-labs/agent-skills --all -a codex -y
```

For GitHub Copilot:

```bash
npx skills add vercel-labs/agent-skills --all -a github-copilot -y
```

The repository keeps this integration documented so a fresh clone can reproduce the same skill set. Do not commit secrets or Vercel tokens.
