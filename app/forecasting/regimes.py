"""Historical regime templates used by BabiMind's analog layer.

These are labels and priors, not hard-coded forecasts. Similarity must still be
measured from actual market observations before a template can influence a
forecast.
"""

HISTORICAL_REGIMES = {
    "1396_1399_cycle": {
        "start": "1396-12",
        "end": "1399-12",
        "label": "FX-inflation liquidity bull -> acceleration -> reversal",
        "notes": [
            "multi-year currency/inflation repricing",
            "accelerating equity participation",
            "extreme positive feedback into mid-1399",
            "post-peak distribution and drawdown",
        ],
    },
    "1391_fx_shock": {
        "start": "1391-01",
        "end": "1391-12",
        "label": "FX/inflation shock regime",
        "notes": ["currency shock", "inflation repricing", "rapid nominal repricing"],
    },
    "1397_1398_repricing": {
        "start": "1397-01",
        "end": "1398-12",
        "label": "currency repricing and commodity-led expansion",
        "notes": ["FX repricing", "commodity exposure", "equity rerating"],
    },
    "1401_1402_inflation_wave": {
        "start": "1401-01",
        "end": "1402-12",
        "label": "inflation/FX-driven equity wave",
        "notes": ["currency pressure", "inflation expectations", "rotation across sectors"],
    },
    "1403_1405_transition": {
        "start": "1403-01",
        "end": "1405-12",
        "label": "policy/geopolitical transition regime",
        "notes": ["policy uncertainty", "energy constraints", "geopolitical risk"],
    },
}


def regime_labels() -> list[str]:
    return list(HISTORICAL_REGIMES)
