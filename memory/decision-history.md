# Decision History / Model Memory

## Record DH-2026-08-21-001
- `timestamp`: 2026-08-21
- `model`: Babi Hoosh + Tasmim
- `subject`: ZMLI7070 / FMLI call analysis
- `model_version`: graph-v1
- `status`: partial validation
- `historical_model_score`: 86/100
- `important_correction`: Earlier analysis used an inconsistent strike/premium record; historical contract parameters must be treated as model-history until independently verified.
- `validated_observation`: The option materially outperformed the underlying over the observed period, consistent with leverage/convexity thesis.
- `not_yet_validated`: Exact entry-time option return, IV path, Greeks path and OI path.
- `anti_hindsight`: Do not upgrade the score without a timestamped entry snapshot and later observed outcome.

## Model memory rules
1. Preserve every prediction with timestamp and model version.
2. Preserve political/economic decisions and actor states as time-indexed records.
3. Store hypotheses separately from verified observations.
4. Store corrections as new records rather than deleting historical reasoning.
5. Every backtest must compare information available at prediction time with information observed afterward.
6. Calibration must evaluate probability quality, not only directional accuracy.

## Integrated model layers
- Decision / political network
- Game theory
- Dynamic systems
- Economic variables
- Market regime / rotation / liquidity
- Codal and fundamentals
- Market data
- Price action
- Technical analysis and indicators
- Options / Greeks / IV / OI
- Probability / expected value
- Backtest / calibration
