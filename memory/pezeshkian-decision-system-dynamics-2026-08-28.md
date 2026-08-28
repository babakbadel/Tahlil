# BabiMind — Pezeshkian Decision System Dynamics

Date: 2026-08-28

## Objective
Model the next likely decisions of President Masoud Pezeshkian as a dynamic decision network rather than a news feed.

## Decision model
For each candidate decision, maintain three mutually exclusive scenario paths whose probabilities sum to 100%. Probabilities are evidence-based estimates and must be withheld/marked uncertain when evidence is insufficient; never fabricate precision.

Each scenario propagates through:
1. Immediate decision
2. Advisor/institution response
3. Policy implementation
4. FX, inflation, liquidity, budget and commodity feedback
5. Market reaction (stocks, gold, FX, sectors, options)
6. Political/social feedback
7. Second-order effects
8. New decision pressure on Pezeshkian

## Influence model
Advisor influence is dynamic and topic-specific. Track access, institutional authority, domain relevance, alignment, recent demonstrated impact, information advantage, execution power and reliability. Do not equate formal title with actual influence.

## Feedback loops
- FX depreciation -> inflation pressure -> political pressure -> policy response -> liquidity/FX feedback.
- External tension -> risk premium -> FX/gold -> inflation -> government response.
- De-escalation -> risk premium decline -> FX/gold repricing -> sector rotation -> political/economic feedback.
- Budget deficit -> financing pressure -> liquidity/rates -> inflation/market reaction -> fiscal response.

## Game Theory layer
Model strategic interaction among presidency, economic team, parliament, security institutions, external actors, market participants and the public. Separate announced intent from credible commitment and observed implementation.

## Three-scenario requirement
For every tracked decision, generate:
A) base/continuity path
B) reform/de-escalation path
C) adverse/escalation or alternative path
Then propagate conditional effects. Scenario probabilities must be updated each run from fresh evidence and prior-run calibration.

## Calibration
Persist every forecast with timestamp, evidence, probabilities and eventual outcome. Score Brier/log loss when outcome becomes observable and update feature/influence weights.

## Current trigger
The Hormuz/de-escalation signal is treated as an uncertain geopolitical input, not a confirmed regime change. It affects Game Theory and Decision pressure but must not by itself imply a definite policy decision.

## Data integrity
Prioritize internal Tahlil/API data and authoritative fresh sources. Missing APIs do not block analysis. Missing evidence blocks invented numbers/signals.
