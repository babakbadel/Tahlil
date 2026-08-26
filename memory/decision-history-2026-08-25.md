# Decision History — 2026-08-25 (۳ شهریور ۱۴۰۵)

> Immutable prediction record. Do not overwrite. Outcome is filled only after the next session(s).

## Metadata

| Field | Value |
|-------|--------|
| `decision_id` | `dh-2026-08-25-market-bias` |
| `as_of` | 2026-08-25T14:00:00+03:30 (approx end of Tehran session) |
| `market_session` | 1405/06/03 |
| `model` | Babi Hoosh + Decision Engine |
| `horizon_primary` | 1–5 trading days |
| `status` | open |
| `updated` | 2026-08-26 (post-session review + Macro context added) |

## Observed inputs (evidence as of as_of)

### Market Data
- Index (کل): ~6,223,870 (+123,920 / +2.03%) — later sessions showed continuation toward 6.38M zone on subsequent days
- Index (هم‌وزن): ~1,765,135 (+25,058 / +1.44%) — historical high context
- Breadth: ~87% symbols positive
- Advance-Decline Ratio: ~8.9
- Real money inflow (حقیقی → سهام/حق‌تقدم/صندوق سهامی): ~3.3–3.5 همت
- Residual buy queues: ~9.7 همت
- Market value: elevated (reported peak levels)

### Price Action / Technical
- Clear break of 6.1M and entry into 6.2M+ channel
- Homogeneous move (کل + هم‌وزن aligned) → breadth confirmation
- Index price above key moving averages (20/50 DMA)
- No clear exhaustion signal in end-of-day structure
- No negative divergence vs breadth or equal-weight

### Game Theory
- Retail: net buyer; buy per-capita > sell per-capita
- Legal/institutional: controlled supply, not panic selling
- Rotation: outflow from gold funds / fixed-income → equities
- Hard-asset complex (metals + mining + refining) leading

### Macro / FX / Gold (same-day context)
- USD free market: ~201–205k range (session-day reports around 204.5–204.7k)
- Gold 18k and coin elevated; later sessions showed some cooling
- Inflation / FX expectation cited as equity demand driver
- Policy environment: bank/FX/energy reform talk + inflation control narrative (no new adverse decision event)

### News / Event overlay
- New listing آکو near daily limit; further IPOs planned
- Sector leadership: فملی، شپنا، میدکو and related hard-asset names
- No new time-stamped adverse role change in core person network observed

## Prediction (locked at as_of)

| Scenario | Description | Model weight |
|----------|-------------|--------------|
| A (primary) | Continuation higher with shallow pullbacks | Highest |
| B | Gap-up then consolidation / mild correction | Medium |
| C | Sharp reversal on legal selling or FX/political shock | Low |

**Directional bias:** Long / Risk-On (1–5 days)  
**Confidence:** Medium-High  
**Key invalidation:**  
- Heavy legal supply in index heavyweights in first 30–60 minutes next session  
- Adverse FX/political event  
- AD Ratio sustained below 5 + real money turning negative  

**Key confirmation:** Continued real inflow + positive breadth (AD Ratio > 8 preferred)

## Expected monitoring metrics (next sessions)

1. Real money flow (sign and size)
2. Breadth (% positive) and AD Ratio
3. Legal vs retail in فملی / فارس / پالایشی leaders
4. USD free-market direction vs prior close
5. Residual queue absorption
6. Distance of index to 20/50 DMA (over-extension risk)

## Outcome (fill later — immutable once written)

| Field | Value |
|-------|--------|
| `outcome_session` | _pending_ |
| `index_change_1d` | _pending_ |
| `index_change_5d` | _pending_ |
| `real_flow_1d` | _pending_ |
| `scenario_realized` | _pending_ |
| `error_notes` | _pending_ |
| `brier_or_score` | _pending_ |

## Provenance

- Sources: session aggregation 1405/06/03, market tables, same-day press
- News injection run: same day
- Macro context: free-market USD and gold reports contemporaneous with session
- Rule: no look-ahead; only information available by end of 1405/06/03 session for the locked prediction
- Post-session note (2026-08-26): subsequent sessions showed continued strength; still treat original lock as immutable for scoring

## Model notes for next run

- Breadth and AD Ratio should be treated as first-class features
- Macro layer (USD + gold) must be filled daily going forward
- Invalidation rules above are binding for bias change
