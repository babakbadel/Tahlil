# BabiMind Historical Forecasting

BabiMind now has a dedicated forecasting layer in addition to observation and decision layers.

## Pipeline

1. Build a historical daily feature table from TSETMC/Codal/macro/FX/gold/energy/news features.
2. Add forward targets for 1, 5, 20 and 60 trading days.
3. At every forecast date, fit only on observations strictly before that date.
4. Standardize features and find nearest historical analogs.
5. Weight analogs by similarity and estimate conditional return distributions.
6. Report probability, expected return, quantiles, drawdown proxy, sample count and confidence.
7. Validate with walk-forward backtesting and track directional accuracy and Brier score.

## 1396-1399 case study

The period from Esfand 1396 through the end of 1399 is explicitly registered as a historical regime template. It must not be treated as a deterministic repeat of 1405. Its influence comes only from measured similarity between the current feature vector and historical observations.

This avoids the common error of saying `USD up => 1399 repeats`.

## Required features

Recommended core features:

- index and sector returns/volatility
- USD/IRR and gold
- liquidity and money-flow measures
- turnover/value traded
- market breadth
- interest-rate and inflation proxies
- commodity prices and oil
- energy/utility constraints
- geopolitical/policy event scores
- valuation and earnings features for symbol-level forecasts

## Forecast horizons

- 1 trading day: tactical
- 5 trading days: short swing
- 20 trading days: monthly regime
- 60 trading days: medium-term regime

## Leakage rule

No feature may contain information unavailable at the forecast timestamp. Forward targets are evaluation-only and are never used as model inputs. Every reported accuracy number must come from walk-forward evaluation, not an in-sample fit.

## Current limitation

The repository does not yet contain the complete multi-year daily feature panel. The engine is therefore implemented and ready for ingestion, but no claim of calibrated live accuracy should be made until the historical panel is backfilled and the walk-forward benchmark is run.
