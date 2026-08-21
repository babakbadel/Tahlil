# Option Ranking Log — 2026-08-21

## Trigger
User requested that every option-market check run the full operations and persist them as repository memory/log + graph.

## Mandatory operations
- Verify current date/session and fresh market data.
- Remove expired contracts before any ranking.
- Verify expiry, T, strike, spot, moneyness and break-even.
- Calculate/verify Black-Scholes fair value where assumptions permit.
- Obtain IV/HV and Greeks (Delta/Gamma/Theta/Vega/Rho) from live/reliable data; never invent missing values.
- Check OI, volume, bid/ask, spread and liquidity.
- Evaluate probability ITM, leverage, convexity, expected payoff and risk.
- Integrate macro/economic variables, Decision History, government/advisor network, Game Theory and Dynamic Systems.
- Integrate Codal/fundamental, price action and technical signals.
- Backtest timestamped predictions and retain calibration/error history.
- Produce a ranked active universe with confidence and explicit data gaps.

## Corrective event
ZHERM5034 and ZHERM5033 were previously surfaced despite expiry 1405/05/28. They must be excluded from the active universe after 1405/05/28. They may remain in historical/backtest records.

## Anti-hindsight
A historical prediction record is immutable. New data creates a new run/version; it must not overwrite the old prediction or outcome.

## Graph links
Market Data -> Expiry Filter -> Option Greeks/Pricing -> Liquidity -> EV -> Macro -> Decision -> Game Theory -> Dynamic Systems -> Fundamentals/Technical -> Backtest -> Ranking -> Decision History -> Knowledge Graph.
