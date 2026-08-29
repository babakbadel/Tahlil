# TSE Option integration

Upstream option-analysis/data source integrated into BabiMind:
- https://github.com/sm-sokout/tse-option

## Role in BabiMind
This integration is an auxiliary option-market source. Repository-owned snapshots remain the primary evidence when available. Data from this source must be cross-checked and must not overwrite synchronized project data without validation.

## Planned/active uses
- option-chain discovery
- strike/expiry structure
- liquidity and open-interest cross-checks
- option pricing/Greeks where the upstream source provides them
- validation against MarketWatchPlus and OptionMarketWatch snapshots

## Data policy
Do not invent IV, Delta, Gamma, Theta, Vega, timestamps, or prices when unavailable. Record missing fields as data gaps and preserve source provenance.
