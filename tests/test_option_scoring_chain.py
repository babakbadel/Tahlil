import json
import pytest
from scripts import score_options_babimind_scenarios as scenarios
from scripts import risk_adjusted_options_babimind as risk


@pytest.mark.parametrize('option_type,delta', [('CALL', .55), ('PUT', -.55)])
def test_scenario_to_risk_preserves_contracts_and_review_gate(tmp_path, monkeypatch, option_type, delta):
    ranked = tmp_path / 'ranked.json'
    scenario = tmp_path / 'scenario.json'
    risk_output = tmp_path / 'risk.json'
    row = {'symbol': 'contract', 'option_type': option_type, 'underlying': 'فملی', 'strike': 100,
           'underlying_price': 100, 'price': 5, 'volume': 100, 'open_interest': 200,
           'days_to_expiry': 45, 'iv': .4, 'delta': delta, 'theta': -.01, 'time_value': 5,
           'decision': 'REVIEW_REQUIRED'}
    ranked.write_text(json.dumps({'status': 'partial', 'source_event_time': None, 'records': [row]}))
    for module, source, output in ((scenarios, ranked, scenario), (risk, scenario, risk_output)):
        monkeypatch.setattr(module, 'SRC', source)
        monkeypatch.setattr(module, 'OUTJ', output)
        monkeypatch.setattr(module, 'OUTM', output.with_suffix('.md'))
        module.main()
    result = json.loads(risk_output.read_text())
    assert result['record_count'] == 1
    assert result['status'] == 'partial'
    assert result['contracts'][0]['decision'] == 'REVIEW_REQUIRED'
    assert result['contracts'][0]['risk_reward_ratio'] == 3
    assert result['contracts'][0]['risk_adjusted_score'] > 0


def test_scenario_without_losses_has_unknown_reward_risk():
    _, rr = risk.calc({'babimind_scenario_score': 80, 'scenario_pnl_pct': {'+10%': 20, '-10%': 5}})
    assert rr is None
