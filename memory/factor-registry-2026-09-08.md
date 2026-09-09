# Factor Registry Memory — 2026-09-08

## Run outcome
- Fresh external evidence strengthened the **commodity impulse**: Brent near $98–99/bbl and copper at record/high levels.
- **Geopolitical risk** remains high and is now a first-order market factor, not background noise.
- Domestic equities retain a **bullish but fragile** regime according to recent market-pulse reporting and the prior internal graph baseline.
- Inflation/rate risk increased; no new verified policy-rate decision was found in this run.
- No current option-chain snapshot, same-day internal MarketWatch snapshot, or fresh broad Codal sweep was verified; these remain explicitly missing.

## Model updates
- Keep the regime label as: `risk-on equity impulse under macro/geopolitical stress`.
- Apply correlation control: do not count oil shock, geopolitics, inflation and rates as four independent bullish/bearish votes; aggregate them as one macro-risk cluster with subcomponents.
- Aggregate copper, supply tightness, AI/grid demand and exporter earnings as one commodity/operating-leverage cluster unless independent data confirm separation.
- Do not issue an options signal without current IV/Greeks/OI/liquidity.
- Keep missing-data policy: `MISSING_IS_NOT_ZERO`; unavailable is not neutral.

## Tahlil commit
- `3a65257c7b1309e14a16de925b90f0f53ef2a014`
- Report: `reports/daily_factor_registry_2026-09-08.json`
