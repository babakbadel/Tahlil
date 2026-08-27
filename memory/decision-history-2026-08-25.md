# Decision History — 2026-08-25 (۳ شهریور ۱۴۰۵)

> Immutable prediction record. Do not overwrite original lock. Outcome filled after next session(s).

## Metadata

| Field | Value |
|-------|--------|
| `decision_id` | `dh-2026-08-25-market-bias` |
| `as_of` | 2026-08-25T14:00:00+03:30 (approx end of Tehran session) |
| `market_session` | 1405/06/03 |
| `model` | Babi Hoosh + Decision Engine |
| `horizon_primary` | 1–5 trading days |
| `status` | closed (outcome recorded) |
| `updated` | 2026-08-27 (outcome filled from 1405/06/04 session) |

## Observed inputs (evidence as of as_of)

### Market Data
- Index (کل): 6,223,877 (+123,921 / +2.03%)
- Index (هم‌وزن): 1,765,135 (+25,058 / +1.44%)
- Breadth: ~87% symbols positive
- Advance-Decline Ratio: ~8.9
- Real money inflow: ~3.33 همت
- Buy power ratio: ~1.19

### Price Action / Technical
- Break of 6.1M and entry into 6.2M channel
- کل + هم‌وزن aligned
- Price above key MAs; no negative divergence vs breadth

### Game Theory
- Retail net buyer
- Rotation from gold/FI funds into equities
- Hard-asset complex leading (metals, mining, refining)

### Macro / FX / Gold (same-day context)
- USD free market elevated (~200–205k range in session reports)
- Inflation / FX expectation cited as demand driver

## Prediction (locked at as_of)

| Scenario | Description | Model weight |
|----------|-------------|--------------|
| A (primary) | Continuation higher with shallow pullbacks | Highest |
| B | Gap-up then consolidation / mild correction | Medium |
| C | Sharp reversal on legal selling or FX/political shock | Low |

**Directional bias:** Long / Risk-On (1–5 days)  
**Confidence:** Medium-High  

**Key invalidation:** Heavy legal supply early next session, adverse FX/political event, AD Ratio sustained < 5 + real money negative  
**Key confirmation:** Continued real inflow + positive breadth

## Outcome (recorded 2026-08-27 from session 1405/06/04)

| Field | Value |
|-------|--------|
| `outcome_session` | 1405/06/04 (۴ شهریور ۱۴۰۵) |
| `index_close_next` | 6,386,576 |
| `index_change_1d` | +162,698 (~+2.61%) |
| `equal_weight_change_1d` | +37,638 (~+2.13%) |
| `real_flow_1d` | ~+4.6 همت (reports ~4.6–4.9 همت; strongest day of week context) |
| `scenario_realized` | **A (primary)** — continuation higher; no shallow pullback yet, full risk-on extension |
| `error_notes` | Bias correct. Magnitude underestimated (expected shallow path; actual was strong second-day continuation). Breadth and real-flow confirmation both hit. |
| `brier_or_score` | Direction correct; scenario weight A validated. Score: High (directional) / Medium (path detail) |
| `invalidation_hit` | No |
| `macro_note` | USD free market cooled slightly (~199.5–200.5k range reported) while equities accelerated → supportive of risk_on_equity regime |

## Provenance

- Lock sources: session 1405/06/03 aggregation
- Outcome sources: end-of-day reports for 1405/06/04 (index close 6,386,576; +2.61%; equal-weight +2.13%; real inflow multi-hemt)
- Rule: original prediction text unchanged; outcome is append-only
