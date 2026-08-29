# Economic Variable Registry

This registry defines the macro variables that can propagate through the analysis graph.

| Variable | Direction of analysis | Typical downstream nodes |
|---|---|---|
| USD/IRR | FX regime, expectations, import/export economics | exporters, FMLI, valuation |
| Inflation | purchasing power, cost pressure, expectations | rates, FX, equities |
| Liquidity | risk appetite and asset demand | market regime, sectors, stocks |
| Policy rates | discount rate and financing conditions | valuation, banks, equities |
| Money base | monetary impulse | liquidity, inflation, FX |
| Budget deficit | fiscal pressure and financing needs | liquidity, rates, FX |
| Energy prices/cost | production cost and industrial margin | metals, miners, manufacturers |
| Exports/imports | external balance and company sales | FX, exporters, industries |
| Copper price | global demand and FMLI revenue sensitivity | FMLI, options |
| Global metals regime | commodity beta and risk appetite | FMLI, mining/metal sector |
| Sanctions/geopolitical risk | trade friction and risk premium | FX, commodities, equities |
| GDP/growth | demand and earnings cycle | sectors, companies |
| Real rates | valuation and savings/investment incentives | equities, FX, gold |
| Trade policy | export competitiveness and supply chain | FMLI and industry |

## Required metadata
Each stored observation should include:
- `variable_id`
- `event_time`
- `value`
- `unit`
- `source`
- `release_time`
- `revision_status`
- `confidence`

## Propagation rule
`economic variable -> policy/actor reaction -> market regime -> sector -> company -> symbol -> option -> decision`

No macro variable should be treated as an isolated signal. The graph evaluates interaction, lag, regime and uncertainty.
