# FMLI Option Model Run — 2026-08-22

## Data-quality gate
- Today is Saturday 1405/05/31 (2026-08-22); Tehran cash market is closed.
- Latest underlying session verified: 1405/05/29, FMLI last 18,530, close 18,690; source chain includes TSETMC-derived Tindex.
- Therefore option quotes found on public pages are historical snapshots with different timestamps. They must NOT be represented as today's synchronized bid/ask/OI dataset.

## Verified active expiry
- FMLI option series examined: expiry 1405/07/08 (2026-09-30), which is still in the future on this run.
- Calls verified: ZMLI7064 K=15,000; ZMLI7065 K=16,000; ZMLI7066 K=18,000; ZMLI7067 K=20,000; ZMLI7068 K=22,000; ZMLI7069 K=24,000; ZMLI7070 K=26,000; ZMLI7071 K=28,000; ZMLI7072 K=30,000.
- Verified puts with usable public snapshots: TMLI7061 K=12,000; TMLI7062 K=13,000; TMLI7066 K=18,000; TMLI7068 K=22,000. Coverage is incomplete for the full put chain.

## Public snapshot observations
- ZMLI7064: 9,450; volume 126; snapshot 1405/05/23.
- ZMLI7065: 5,846; volume not surfaced in current search result; snapshot 1405/05/11.
- ZMLI7066: 5,900; volume 786; snapshot data is older than the underlying reference.
- ZMLI7067: 5,099; volume 128; snapshot 1405/05/14.
- ZMLI7068: 3,310; volume 20,183; snapshot 1405/05/16.
- ZMLI7069: 2,704; volume 5,953; snapshot 1405/05/14.
- ZMLI7070: 2,700; volume 3,581; snapshot 1405/05/18.
- ZMLI7071: 1,200; volume 5,556; snapshot 1405/05/28.
- ZMLI7072: 520; volume 464; snapshot 1405/05/10.

## Model methodology
- Black-Scholes European model used only as a comparative model.
- Illustrative risk-free rate: 30%; T approximately 39 calendar days from 1405/05/31 to 1405/07/08.
- IV is reverse-solved from each historical option price; it is NOT official live IV.
- Greeks are model-derived and therefore inherit the timestamp/price mismatch.
- Hard rule: no final trading rank when option and underlying timestamps are not synchronized.

## Structural result
- Current Spot ~18,530 puts 7068/7070 etc. far OTM; 7066 is near ATM.
- Among calls, 7068 has the strongest combination of moderate OTM strike and observed volume, but its quote is historical; 7069 is next; 7070 is more convex but more OTM and has a high model-implied volatility from the observed price.
- Deep ITM calls 7064/7065 have higher Delta but poor observed liquidity and/or very high model IV.
- Put ranking is provisional because the public chain is incomplete; TMLI7066 is the only near-ATM put with a usable public snapshot in the retrieved set.

## Fundamental context
- FMLI Q1 1405 reported EPS 691 IRR and net profit 725,886,485 million IRR, +262% YoY.
- April 1405 monthly sales: 513,701,118 million IRR; four-month cumulative sales: 1,811,275,024 million IRR.
- These support the bullish fundamental branch but do not override option valuation/liquidity gates.

## Decision
- No final "best FMLI option today" is declared until synchronized live quote + bid/ask + OI + volume + IV are available for the full chain.
- Provisional structural leader: ZMLI7068, followed by ZMLI7069 and ZMLI7070.
- This run supersedes any prior ranking only for the new timestamp; historical rankings remain immutable.
