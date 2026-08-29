# Dynamic Systems Layer

## Purpose
Model economic and market behavior as time-dependent systems with stocks, flows, delays, feedback loops, shocks, and regime changes.

## Core stocks
- Liquidity
- Money base
- Inflation expectations
- Corporate cash flow / retained earnings
- Fiscal imbalance
- FX reserves / external balance
- Inventory and production capacity

## Core flows
- Credit creation
- Government spending
- Tax receipts
- Export/import flows
- Capital inflow/outflow
- Money velocity
- Production and sales

## Important delays
- Policy decision -> implementation
- FX move -> reported earnings
- Copper price -> realized sales price
- Liquidity -> inflation
- Inflation -> FX expectations
- Codal disclosure -> market repricing

## Feedback loops

### FX / inflation loop
`FX ↑ -> import costs ↑ -> inflation ↑ -> inflation expectations ↑ -> FX demand ↑ -> FX ↑`

### Liquidity / asset loop
`Liquidity ↑ -> risk appetite ↑ -> equity demand ↑ -> prices ↑ -> wealth/confidence ↑ -> risk appetite ↑`

### Policy stabilization loop
`Policy credibility ↑ -> expectations volatility ↓ -> precautionary FX demand ↓ -> FX volatility ↓ -> inflation expectations ↓`

### Commodity exporter loop
`Copper ↑ -> FMLI revenue/profit expectations ↑ -> FMLI valuation ↑ -> FMLI demand ↑ -> option demand ↑`

## Dynamic-model rules
1. Every causal edge must have a direction and, where possible, a lag.
2. Strong claims require evidence; correlations are not automatically causal.
3. Regime changes can alter edge strength and even edge direction.
4. Feedback loops must be tested against historical observations.
5. Scenario simulations must expose assumptions and probabilities.
