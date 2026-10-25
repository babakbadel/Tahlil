# BabiMind reliability repair — 2026-10-25

## Observed production failures

- Daily run 40198704540 failed when its generated-output commit was rejected because another workflow had advanced main.
- Market/options run 40180911075 failed installing the legacy pypiHat dependency lxml 4.9.4 on Python 3.13, preventing every collector from running.
- The paired CSV has 42 columns, while the importer required 43, dropping all 466 rows. It also reversed Iranian call/put symbol prefixes. Re-imported summaries must replace old derived summaries before using their call/put counts.

## Repairs

- All output writers use a shared publisher with three fetch/rebase/push attempts and no forced push. Conflicts between generated snapshots favor the publishing run. Concurrent upstream code is preserved. Publishing from feature branches is blocked.
- Stage generated files individually, avoiding silent git-add failure when an optional path does not exist. Retain daily and provider artifacts even on failure.
- Market collection uses Python 3.11; the pinned legacy provider runs in an isolated environment. Optional provider installation cannot stop other collectors. Install the previously absent async/pytsetmc providers.
- Validate collection timestamps and actual provider envelope schemas. Reject missing, stale, future, malformed, failed, or empty collections. Ingest metadata has its own report and cannot overwrite provider health.
- CSV ingestion splits the header-defined call, underlying/date and put sections and imports both paired contracts. Call prefixes are ض and put prefixes are ط. Missing premium stays null. Invalid prices, types, strikes, crossed books, future quotes, and unsynchronized quotes cannot get a final option rank. Completeness scores do not produce BUY/HOLD instructions.
- BRS equity and dedicated option feeds are both requested. Polling runs outside the async event loop and retries transport failures. Missing credentials do not prevent the service from starting or serving health. Responses expose snapshot age and stale/degraded state. Transport exceptions cannot print API keys in URLs.
- The downstream scenario scorer preserves the review gate. Risk scoring reads the actual `records`, scenario P/L, score and expiry fields; it no longer silently emits an empty result. Both call and put stress scenarios flow into the central pipeline and LLM evidence. Reward/risk remains unknown when no scenario loss is available.
- Walk-forward training excludes labels whose horizon is not yet observable. Missing forward labels and drawdowns retain the correct similarity/weight alignment.
- Production no longer executes placeholder decisions dated 2026-08-25. Model readiness and completeness-only option results are included in the central pipeline and LLM evidence.
- An unavailable LLM emits an explicit unavailable report and does not block deterministic processing. It is not ingested as a successful memory result.
- Source health checks run concurrently. SourceArena workflow input passes through an environment variable rather than shell interpolation.
- CI checks Python 3.11/3.13, regression tests, frontend build, and TypeScript. The frontend dependency lock is committed.

## Validation

Local regression tests cover call/put direction, expiry, missing/invalid quotes, timestamp synchronization, dedicated option collection, nonblocking polling, transport failure recovery, credential-free health, secret-safe errors, forecast label maturity, missing historical targets, collection schema/freshness, and publishing over concurrent code/output changes.

`npm run build`, `npm run typecheck`, Python compilation, YAML parsing, and `git diff --check` pass locally. The source-to-pipeline smoke completed in 12.47 seconds: 65 source URLs checked, 18 eligible endpoints, 42 unavailable endpoints. URL availability is operational metadata, not proof of usable financial data. Restricted network access can affect this result.

## Remaining limits

- Live external provider success and GitHub secret configuration must be verified in scheduled/manual production runs. No credentials are added to source.
- Forecasting requires a validated chronological feature panel; production decision generation requires sourced current evidence. These integrations remain explicitly `not_connected`; no probabilities are fabricated.
- Model scores are not calibrated trading recommendations. Missing synchronized quotes, IV, history, or macro data must remain visible.
- Collection timestamps establish recent retrieval, not quote event time. The source catalog's endpoint health must not be mistaken for validated current observations.
- Thread-based network checks have per-call timeouts, but executor shutdown is not a strict process-wide deadline if underlying networking ignores its timeout.
- The model's economic accuracy, provider uptime, and execution at an exact scheduled minute are not guaranteed by passing CI.
