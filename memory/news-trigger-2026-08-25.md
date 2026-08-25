# News Trigger — 2026-08-25

## Automation
- Name: `tahlil-news-scan`
- ID: `760c9d17-b96f-4a77-a462-988d1195402a`
- Schedule: hourly 08:00–14:00 Asia/Tehran, Sat–Wed
- Scope: only project-relevant news (equity market, Codal, macro/FX policy, influence network actors)
- Output: max 5 items, concise; or explicit no-material-news line

## Rules
- No rumors without source
- Feed Decision Engine / Event layer only when material
- Persist digests as `NEWS_DIGEST | date | N items`
