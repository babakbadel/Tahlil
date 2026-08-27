# Outcome Record — dh-2026-08-25-market-bias
## Linked decision
- decision_id: `dh-2026-08-25-market-bias`
- as_of lock: end of session 1405/06/03 (2026-08-25)
- This file is append-only evaluation. Original prediction remains immutable.

## Realized path (through 1405/06/04)

| Metric | Value | Notes |
|--------|-------|-------|
| index_total 1405/06/03 close | ~6,223,877 | lock day |
| index_total 1405/06/04 close | 6,386,576 | +162,698 / +2.61% |
| index_equal_weight 1405/06/04 | 1,802,773 | +37,637 / +2.13% |
| real_inflow 1405/06/04 | ~4.6–4.7 همت | strongest day of week in reports |
| breadth 1405/06/04 | ~93% symbols positive | very strong |
| USD free 1405/06/04 | ~199–200k | cooling vs prior ~204k |
| gold 18k / coin | lower vs prior session | cooling with USD |

## Scenario realized
- **Primary scenario A (continuation higher with shallow pullbacks): CONFIRMED for 1d horizon**
- No invalidation triggered (no breadth collapse, no real-money reversal, no adverse FX shock)
- Macro regime remained supportive: equity risk-on while USD/gold cooled

## Score notes
- Directional accuracy (1d): correct (Long)
- Magnitude: stronger than base case (large green day)
- Confidence was Medium-High; outcome supports maintaining or slightly raising confidence on similar breadth+flow setups
- Brier-style note: scenario A had highest weight and occurred

## Lessons for Model Memory
1. High AD Ratio + real inflow + equal-weight confirmation remains a strong 1–5d continuation signal.
2. USD cooling concurrent with equity strength is supportive (risk_on_equity regime), not contradictory.
3. Keep invalidation rules; they correctly stayed inactive.

## Provenance
- Market close figures from same-day/end-of-day press aggregation for 1405/06/04
- Flow figures approximate as reported; treat as high-quality directional evidence
- No look-ahead relative to decision lock date
