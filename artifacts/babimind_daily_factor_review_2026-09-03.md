# BabiMind Daily Factor Review — 2026-09-03

## Data status
- Fresh web/news sources reviewed.
- Internal Tahlil/API snapshots for live Iran market, options, order flow and Codal were not directly available in this run; no synthetic values or signals were generated.
- Public market claims are treated as secondary evidence and require internal validation before promotion to hard signals.

## Regime
**Active regime:** Geo-trade shock + FX stress + stagflation risk.

## Material changes vs previous run
1. **Shock persistence upgraded:** renewed US-Iran strikes and sharply reduced Hormuz traffic indicate the disruption is not a one-day event.
2. **Export monetization gap widened:** Reuters/Kpler/Vortexa reports indicate Iranian crude loadings fell to roughly 220k–255k bpd in August from about 2m bpd in March, while the central bank publicly claims sufficient reserves and readiness to inject up to $2bn. This is a credibility/accessibility gap, not proof that reserves are absent.
3. **FX stress intensified:** public trackers/reporting place the free-market rial above 2.2m per USD; treat as directional evidence only until Tahlil/API confirms.
4. **Global discount-rate pressure increased:** Brent near $95 and higher global yields increase imported inflation and financing pressure.
5. **Domestic equity breadth signal remains unverified:** recent public reports claim a record high and strong retail inflows, but no current Tahlil snapshot was available; do not convert these into a trading signal.

## Factor ledger
| Factor | Direction | Intensity | Freshness | Confidence | Evidence / note |
|---|---|---:|---|---:|---|
| Hormuz / shipping | Negative for Iran stability | 5/5 | Very fresh | 4/5 | Reuters reports only 4 vessels vs 13 ten-day average; route remains unstable. |
| Iranian oil exports | Negative | 5/5 | Fresh | 4/5 | Reuters/Kpler/Vortexa report Aug loadings ~220k–255k bpd vs ~2m bpd in Mar. |
| Accessible FX | Negative / uncertain | 5/5 | Fresh | 3/5 | CBI intervention claim conflicts with market stress; reserve accessibility not independently verified. |
| Rial expectations | Negative | 5/5 | Very fresh | 3/5 | Public reports place rial above 2.2m/USD; validate via internal feed. |
| Inflation expectations | Negative | 5/5 | Fresh | 4/5 | FX shock + oil/shipping shock + supply disruption. |
| Global oil | Mixed | 4/5 | Very fresh | 5/5 | Brent around $95: supports nominal oil value but raises global/imported inflation. |
| Global rates/yields | Negative for risk assets | 3/5 | Fresh | 4/5 | Higher yields and rate-hike expectations raise discount rates. |
| Fiscal dominance risk | Up | 4/5 | Fresh | 3/5 | Lost oil FX plus higher support costs; monetization not confirmed. |
| Trade corridor fragility | Negative | 5/5 | Fresh | 4/5 | Hormuz, insurance, settlement and route substitution remain constrained. |
| Policy credibility gap | Worsening | 4/5 | Fresh | 3/5 | Public reserve/intervention claims coexist with record FX stress; measure, do not assume. |
| Market breadth / retail flow | Unknown | — | Stale/partial | 1/5 | Public reports exist, but no current Tahlil snapshot; no signal issued. |
| Options IV/skew/OI | Unknown | — | No data | 1/5 | No internal option chain snapshot available. |
| Codal/fundamental | Unknown | — | No data | 1/5 | No current Codal/API batch available. |

## Correlation control
Clustered into one **Geo-Trade Shock Cluster**: strikes, Hormuz traffic, oil price, shipping risk premium, and insurance/freight. These are not counted as five independent shocks.

Separated conceptually:
- `Gross FX reserves` vs `Accessible FX`
- `Oil physically moving` vs `Oil revenue received`
- `Official intervention capacity` vs `Intervention credibility`
- `Index level` vs `Breadth/retail participation`

## Newly discovered / watched factors
- `Shock Persistence`
- `Export Monetization Gap`
- `Intervention Credibility / Sterilization Risk`
- `Trade Corridor Fragility`
- `FX-Asset Conversion Speed`
- `Policy Credibility Gap`

These remain **watch/candidate** factors until historical Tahlil/API data supports lagged, partial, regime-stable and out-of-sample relationships.

## Scenario update
- **Base:** prolonged disruption without full system break; continued FX/inflation pressure.
- **Positive:** verifiable de-escalation + restoration of shipping and oil monetization.
- **Negative:** further strikes/blockade + banking/payment restrictions.
- **Tail:** banking stress + rapid FX deterioration + fiscal monetization; not confirmed.

## System dynamics
`Conflict intensity -> Hormuz traffic -> oil monetization -> accessible FX -> rial expectations -> inflation -> fiscal stress -> monetization risk`

The key state variable today is **duration of disruption**, not the headline alone.

## Model memory update
- Increase weight of `Shock Persistence` and `Export Monetization Gap`.
- Keep `Accessible FX` as a distinct state variable.
- Do not promote public-market equity/option claims to hard signals without Tahlil/API confirmation.
- Preserve uncertainty tags and source provenance for every factor.
