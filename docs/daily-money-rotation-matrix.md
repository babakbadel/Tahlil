# Daily Money Rotation Matrix

## Purpose
A BabiMind/Tahlil decision layer for detecting visible and hidden liquidity rotation in Iran equities from end-of-day market data.

## Daily input requested from user at 18:00
For selected symbols/sectors, collect: last and close price, day/week range, trades, volume, value, monthly average volume, real/legal buy and sell volume, buyer/seller counts, order-book levels, latest disclosures/news, and relevant sector peers.

## Core signals
1. Price response versus market and sector peers.
2. Volume / monthly-average-volume ratio.
3. Net real-person flow = real buy volume - real sell volume.
4. Net legal-person flow = legal buy volume - legal sell volume.
5. Real-person buy/sell per-capita (average transaction size).
6. Order-book pressure and queue persistence.
7. Relative strength versus sector and market leaders.
8. Valuation as a secondary filter; never use low P/E alone as a buy signal.
9. Fundamental/structural risks and recent disclosures.

## Hidden-money classification
- **Hidden accumulation:** price lags peers while net real flow is positive, volume is at/above normal, and legal selling is absorbed.
- **Confirmed inflow:** price strength + above-normal volume + positive net real flow + stronger buying per-capita.
- **Momentum leader:** strong price/relative strength without meaningful net real flow.
- **Liquidity rotation source:** price positive but net real flow materially negative while legal buyers absorb supply.
- **Supply shortage:** price/queue strong but volume materially below average; do not mistake a low-float ceiling queue for confirmed accumulation.

## Decision rules from 1405/06/24 analysis
- شپنا: hidden-accumulation candidate while it holds 14,000 and real flow stays positive; 14,400 breakout with volume is confirmation. Losing 14,000 invalidates the thesis.
- وبملت: high-quality accumulation candidate; strong real flow (+1.949B shares in the observed session) with +2.81% close and P/E 3.47.
- خساپا: strong auto-sector inflow candidate; +2.397B real net flow and ~110% monthly-average volume. 758 then 788 are key continuation levels; 735 is defense.
- خودرو: weaker than خساپا; near-zero real net flow despite positive price. 766-767 breakout plus fresh real flow is required for confirmation.
- دی: exceptionally strong tape (+626.96M real net flow, ~113% monthly volume, 288M-share buy queue), but structural/listing risk must be separately checked; low P/E alone is not sufficient.
- فولاد: strongest volume/value confirmation among observed leaders; ~166% monthly volume, but only ~+21M real net flow, so classify primarily as broad-liquidity/volume leadership rather than pure smart-money inflow.
- فملی: strong momentum leader near highs, but only ~+19.9M real net flow; price strength is stronger than evidence of net real accumulation.
- وتجارت: positive price but ~-950M real net flow; treat as a possible liquidity source for rotation, not a broad bank-sector confirmation.
- شبندر/شتران/شبریز: strong price/queues but volume only ~39-45% of monthly averages; classify as supply-shortage/low-float strength until volume confirms.

## Daily output
Produce a ranked matrix with columns: symbol, price strength, volume ratio, net real flow, real buy/sell per-capita, legal flow, order-book strength, relative strength, hidden-money score, risk flags, key levels, and next-session confirmation/invalidation trigger.

## Important discipline
Do not infer "money moved from sector A to sector B" merely because both sectors are green or one lags. Require evidence of a source (negative real flow/weakening) and destination (positive real flow/volume/price confirmation). Use other symbols as sensors unless the user explicitly asks for a trade recommendation.
