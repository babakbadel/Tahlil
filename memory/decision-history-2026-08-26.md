# Decision History — 2026-08-26 (۴ شهریور ۱۴۰۵)

> Immutable prediction record. Do not overwrite. Outcome filled only after subsequent session(s).

## Metadata

| Field | Value |
|-------|--------|
| `decision_id` | `dh-2026-08-26-market-bias` |
| `as_of` | 2026-08-26T14:00:00+03:30 (approx end of Tehran session) |
| `market_session` | 1405/06/04 |
| `model` | Babi Hoosh + Decision Engine |
| `horizon_primary` | 1–5 trading days |
| `status` | open |
| `prior_decision` | dh-2026-08-25-market-bias (scenario A realized) |

## Observed inputs (evidence as of as_of)

### Market Data
- Index (کل): 6,386,576 (+162,698 / +2.61%) — new high zone; near 6.4M psychological
- Index (هم‌وزن): 1,802,773 (+37,638 / +2.13%)
- Breadth: very strong (reports of ~95% green intraday; heavy buy queues)
- Real money inflow: ~4.6–4.9 همت (strongest recent day in weekly context)
- Market value: ~182+ thousand همت context

### Price Action / Technical
- Clean continuation from 6.22M to 6.38M
- کل and هم‌وزن still aligned → breadth confirmation
- Price further extended above short MAs; over-extension risk rising
- No negative divergence yet vs equal-weight or reported breadth

### Game Theory
- Retail still net buyer; buy queues dominant
- Hard-asset / liquidity leadership continues (metals, energy-linked, banks mixed)
- Legal supply absorbed; no panic distribution signal in index heavyweights

### Macro / FX / Gold
- USD free market: ~199.5–200.5k (modest cooling vs prior elevated prints)
- Equity up + FX softer = supportive of `risk_on_equity` regime
- Gold/coin mixed/cooling in some reports — consistent with rotation into equities

### Event / Policy
- No new adverse geopolitical shock timed to session close
- Momentum + FOMO risk elevated after two strong days

## Prediction (locked at as_of)

| Scenario | Description | Model weight |
|----------|-------------|--------------|
| A (primary) | Continuation / grind higher with possible shallow intraday pullbacks; test of 6.4M area | Highest |
| B | Consolidation / time correction after extension; index holds above 6.25–6.30M | Medium |
| C | Sharp mean-reversion if legal supply hits early or FX re-spikes | Low–Medium |

**Directional bias:** Long / Risk-On (1–5 days), but with tighter risk controls  
**Confidence:** Medium (direction) / Medium-Low (path — extension risk)  

**Key invalidation:**
- AD Ratio collapse (sustained < 5) + real money negative
- Early-session heavy legal supply in فملی / index heavyweights
- Sharp USD free-market re-acceleration with equity outflow

**Key confirmation:**
- Real inflow remains positive
- هم‌وزن stays constructive (not pure heavyweight squeeze)
- Index holds above prior breakout zone on any dip

## Expected monitoring metrics (next sessions)

1. Real money flow sign/size
2. AD Ratio / % positive
3. Distance to 20/50 DMA (over-extension)
4. USD free close vs prior day
5. Buy-queue residual vs sell pressure in first 30–60 minutes

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

- Sources: end-of-day 1405/06/04 market reports (index, equal-weight, flow, breadth proxies)
- Prior decision outcome linked: dh-2026-08-25 realized Scenario A
- Rule: no look-ahead beyond session close 1405/06/04
