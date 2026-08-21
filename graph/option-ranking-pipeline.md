# Option Ranking Pipeline

## Rule
Every option-ranking run must begin with a fresh market-data check. Never rank expired contracts.

## Required validation order
1. Current date/time and market session
2. Active universe: `expiry > now`
3. Underlying spot and contract specification
4. Expiry / time-to-maturity (T)
5. Strike, moneyness, intrinsic value, time value, break-even
6. Black-Scholes (or appropriate pricing model)
7. Implied volatility (IV), historical volatility (HV)
8. Greeks: Delta, Gamma, Theta, Vega, Rho
9. OI, volume, bid/ask, spread and liquidity
10. Probability ITM / expected payoff / convexity / leverage
11. Macro variables and economic regime
12. Decision layer: government policy, actors and advisors, time-stamped
13. Game theory: strategic behavior of relevant actors
14. Dynamic systems: feedback, lags, stocks/flows
15. Fundamentals/Codal, price action and technical analysis
16. Backtest and calibration against a timestamped prediction
17. Produce ranking and confidence, with unavailable fields explicitly marked.

## Anti-hindsight rule
Historical rankings must never be retroactively changed. A new run creates a new timestamped version. Expired contracts remain in history but are excluded from the active investment universe.

## Current lesson
Contracts such as ZHERM5034/ZHERM5033 were incorrectly surfaced after their 1405/05/28 expiry. This is now a hard pre-ranking exclusion rule.
