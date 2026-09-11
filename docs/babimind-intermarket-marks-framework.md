# BabiMind Intermarket + Marks Framework

## Purpose

این سند دانش عملیاتی استخراج‌شده از چارچوب‌های عمومی و قابل‌استناد چهار اثر زیر را به BabiMind تبدیل می‌کند. متن کتاب‌ها کپی نشده و این سند جایگزین مطالعه نسخه قانونی کتاب‌ها نیست.

1. John J. Murphy — *Intermarket Technical Analysis* (1991)
2. John J. Murphy — *Trading with Intermarket Analysis* (2012/2015 editions)
3. Howard Marks — *Mastering the Market Cycle* (2018)
4. Howard Marks — *The Most Important Thing* (2011)

Murphy بر رابطه بین سهام، اوراق، کالاها و ارزها، تخصیص دارایی، چرخش بخشی و چرخه کسب‌وکار تأکید می‌کند. Marks بر چرخه‌ها، ریسک، قیمت در برابر ارزش، تفکر مرتبه دوم، خلاف‌جمع‌بودن، صبر و تشخیص جایگاه فعلی در چرخه تأکید می‌کند.

## Operational model

BabiMind باید از single-market analysis به **cross-market state estimation** حرکت کند.

### Core intermarket map

- Bonds / real yields → liquidity and equity valuation regime
- USD / FX → commodities, imported inflation and domestic risk appetite
- Copper / industrial commodities → global growth and cyclicality
- Oil → inflation, transport/input costs and Iran fiscal/external-balance channels
- Gold → real-rate, FX, risk and monetary-confidence signal
- Equities → sector rotation and forward economic expectations
- Cash / fixed income → opportunity cost and destination of defensive capital
- Housing / auto / other real assets in Iran → inflation hedge and domestic liquidity absorption

### Iran adaptation

The model must not assume textbook US relationships are stable in Iran. Each relationship receives a regime-dependent sign and confidence score.

Minimum Iran cross-market state:

`inflation + liquidity growth + money/base-money growth + real rate + USD + gold + housing + fixed income + auto + Tehran equities + commodities + oil + China/global cycle`

Then estimate:

`relative return + liquidity + volatility + valuation + policy shock + narrative/positioning → capital rotation probability`

## Marks layer

For every important asset or sector, BabiMind asks:

1. What is the first-level consensus?
2. What is the second-level view: what is already priced in?
3. Where are we in the cycle?
4. Is risk rising because price/value has become stretched?
5. What is the downside if the thesis is wrong?
6. Is the opportunity asymmetric enough to justify action?
7. What evidence would invalidate the thesis?
8. Are we being paid for taking the risk?

No signal is upgraded merely because it is popular or has strong recent momentum.

## Cycle engine

BabiMind maintains a regime vector:

- growth: accelerating / stable / decelerating
- inflation: rising / stable / falling
- liquidity: expanding / neutral / contracting
- real rates: deeply negative / negative / neutral / positive
- risk appetite: risk-on / neutral / risk-off
- commodity regime: bullish / neutral / bearish
- currency regime: appreciating / stable / depreciating
- credit stress: low / medium / high

The cycle state must be timestamped. Historical conclusions must not leak future information.

## Rotation engine

For each market/sector calculate:

`RotationScore = 0.25 RelativeStrength + 0.20 Flow + 0.15 MacroFit + 0.15 ValuationGap + 0.10 CycleFit + 0.10 Catalyst + 0.05 Positioning`

These weights are priors, not immutable truths. They must be calibrated against BabiMind history and may be changed only with an explicit versioned model update.

A separate **RiskPenalty** is applied for:

- policy uncertainty
- liquidity deterioration
- crowded positioning
- extreme valuation
- negative earnings revision
- event concentration
- data-quality problems

## Second-level thinking gate

Before issuing BUY / HOLD / REDUCE / SELL, compare:

`BabiMind thesis` vs `consensus / already-priced expectation`.

If the thesis is bullish but the positive information is already fully reflected in price, confidence must be reduced even when fundamentals are good.

## Intermarket confirmation rules

### Strong confirmation

At least 3 independent cross-market signals agree and none of the high-weight risk gates is active.

### Mixed

Signals conflict. Output HOLD / WAIT unless expected value is clearly asymmetric.

### Divergence warning

If price rises while flow, relative strength, macro fit or confirming markets deteriorate, flag **Intermarket Divergence** rather than automatically following price.

### Regime break

If historical correlation/sign changes materially, invalidate the old relationship and reduce confidence until recalibrated.

## Options extension

Options are downstream of the intermarket regime, not isolated instruments.

For an option on an underlying:

`OptionScore = UnderlyingIntermarketScore + DirectionalEdge + IVEdge + OI/Flow + GreeksFit - EventRisk - LiquidityPenalty`

A bullish underlying is insufficient for a call if IV is excessively expensive, time decay is dominant, liquidity is weak, or the catalyst is already priced.

## Required BabiMind output

Every major daily run should expose:

- Intermarket regime
- Cycle position
- strongest confirming relationships
- strongest divergences
- capital-rotation map
- consensus vs second-level view
- risk asymmetry
- affected sectors/symbols
- options implications
- confidence and data freshness
- invalidation conditions

## Source discipline

The framework is a model layer, not a claim that the books predict Iranian markets perfectly. Relationships must be tested against Iranian historical data and can change by regime.
