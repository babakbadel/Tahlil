# BabiMind / Babi Hoosh — Daily Feature Panel Schema

Canonical field list for historical forecasting and Decision Engine inputs.  
Every row is one **trading day** (`session_date` Jalali + Gregorian).  
Leakage rule: no field may use information published after that session's close.

Version: 2026-08-25 (updated 2026-08-26 with Macro block emphasis and AD Ratio)

## A. Identity & calendar

| field | type | notes |
|-------|------|--------|
| `session_date_jalali` | string | e.g. `1405/06/03` |
| `session_date_gregorian` | date | e.g. `2026-08-25` |
| `weekday` | int/string | |
| `is_half_day` | bool | |
| `market_open` | bool | |

## B. Index & breadth

| field | type | notes |
|-------|------|--------|
| `index_total_close` | float | شاخص کل |
| `index_total_return_1d` | float | |
| `index_equal_weight_close` | float | هم‌وزن |
| `index_equal_weight_return_1d` | float | |
| `index_price_close` | float | شاخص قیمت (وزنی-ارزشی) |
| `index_price_return_1d` | float | |
| `index_otc_close` | float | فرابورس |
| `index_otc_return_1d` | float | |
| `pct_symbols_positive` | float | breadth |
| `pct_symbols_negative` | float | |
| `advance_decline_ratio` | float | **AD Ratio = Advances / Declines** (core breadth metric) |
| `n_buy_queues` | int | صف خرید |
| `n_sell_queues` | int | صف فروش |
| `buy_queue_value` | float | همت |
| `sell_queue_value` | float | همت |

## C. Liquidity & flow

| field | type | notes |
|-------|------|--------|
| `value_traded_total` | float | |
| `value_traded_retail_equity` | float | سهام+حق‌تقدم+صندوق سهامی |
| `volume_shares` | float | |
| `trade_count` | int | |
| `real_inflow` | float | ورود پول حقیقی (signed) |
| `real_outflow` | float | optional split |
| `legal_net` | float | if available |
| `buy_per_capita` | float | سرانه خرید |
| `sell_per_capita` | float | سرانه فروش |
| `buy_power_ratio` | float | buy/sell per capita |
| `market_cap_total` | float | ارزش بازار |

## D. Sector / group flows

| field | type | notes |
|-------|------|--------|
| `flow_metals` | float | فلزات اساسی |
| `flow_refining` | float | پالایشی |
| `flow_mining` | float | معادن |
| `flow_petro` | float | پتروشیمی |
| `flow_banks` | float | بانک |
| `flow_auto` | float | خودرو |
| `flow_pharma` | float | دارو |
| `flow_gold_funds` | float | صندوق طلا |
| `flow_fixed_income_funds` | float | درآمد ثابت |

Alternative long format: `(session_date, sector, net_flow)`.

## E. FX, gold, commodities (Macro core)

| field | type | notes |
|-------|------|--------|
| `usd_free_close` | float | دلار آزاد (تومان) |
| `usd_free_return_1d` | float | |
| `usd_official_or_nima` | float | if used |
| `gold_18_close` | float | طلای ۱۸ عیار |
| `gold_ounce_usd` | float | اونس جهانی |
| `coin_emami` | float | سکه امامی |
| `brent_usd` | float | |
| `copper_usd` | float | relevant to metals complex |

## F. Volatility & technical aggregates

| field | type | notes |
|-------|------|--------|
| `index_realized_vol_5d` | float | |
| `index_realized_vol_20d` | float | |
| `index_distance_to_20dma` | float | (close / MA20) - 1 |
| `index_distance_to_50dma` | float | |
| `index_distance_to_200dma` | float | optional |
| `index_rsi_14` | float | optional |
| `price_vs_ma_regime` | string | above_all / mixed / below_all |

## G. Macro / policy / event scores

| field | type | notes |
|-------|------|--------|
| `event_score_geopolitical` | float | [-1,1] or 0–10, documented scale |
| `event_score_policy` | float | |
| `event_score_fx_regime` | float | |
| `inflation_proxy` | float | if available |
| `rate_proxy` | float | سپرده/اوراق if available |
| `person_network_delta` | float/json | change in influence map that day |
| `macro_regime` | string | risk_on_equity / fx_gold_hedge / mixed / risk_off |

## H. Fundamental / Codal (market-level or delayed)

| field | type | notes |
|-------|------|--------|
| `codal_count_material` | int | افشای بااهمیت count |
| `codal_count_earnings` | int | |
| `agg_pe_market` | float | if reliable |
| `agg_ps_market` | float | optional |

## I. Targets (evaluation only — never as inputs)

| field | type | notes |
|-------|------|--------|
| `fwd_return_1d` | float | |
| `fwd_return_5d` | float | |
| `fwd_return_20d` | float | |
| `fwd_return_60d` | float | |
| `fwd_max_drawdown_5d` | float | proxy |

## J. Provenance

| field | type | notes |
|-------|------|--------|
| `source_index` | string | TSETMC / BRS / … |
| `source_flow` | string | |
| `source_fx` | string | |
| `source_gold` | string | |
| `received_at` | datetime | |
| `data_quality` | string | live / delayed / partial |

## Implementation notes

1. Store as daily parquet/csv partitioned by year-month.
2. Walk-forward: train only on rows with `session_date < forecast_date`.
3. Missing values: explicit null + `data_quality` flag; do not silent-fill with future data.
4. Sector flows may be stored long: `(session_date, sector, net_flow)`.
5. Align with `docs/historical_forecasting.md` horizons: 1 / 5 / 20 / 60 days.
6. **AD Ratio and Macro block (E + G) are mandatory daily fields** from this version onward.
7. No-look-ahead is absolute: any field using post-close information invalidates the row for training.

## Link to Decision Engine

Feature panel rows feed:
- Decision History inputs
- Scenario probability scoring
- Regime detection (Risk-On / Risk-Off / Mixed)
- Invalidation checks (breadth collapse, FX shock, flow reversal)
