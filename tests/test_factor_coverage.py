"""Regression checks for issue #5: endpoint health cannot stand in for observations."""
import copy
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts.babimind_factor_coverage import build_report

NOW = datetime(2026, 10, 25, 12, tzinfo=timezone.utc)
CAT = {'version': 1, 'factor_count': 1, 'factors': [
    {'id': 'inflation_cpi', 'name': 'CPI', 'cluster': 'macro', 'sources': ['SCI']} ]}
OBS = {'factor_id': 'inflation_cpi', 'source': 'SCI',
       'timestamp': NOW.isoformat(), 'raw_value': 0, 'normalized_score': 0,
       'confidence': .8, 'max_age_seconds': 3600, 'state': 'ok'}


def report(observations=()):
    return build_report(CAT, observations, NOW)


def test_no_observation_is_unavailable_and_has_full_contract():
    result = report()
    assert result['factor_count'] == 1
    assert result['counts'] == dict(Available=0, Partial=0, Stale=0, Unavailable=1)
    row = result['records'][0]
    for key in ('source', 'timestamp', 'raw_value', 'normalized_score', 'freshness', 'confidence'):
        assert row[key] is None
    assert row['retry_next_run'] and row['signal_weight'] == 0
    assert row['factor_id'] == 'inflation_cpi'


def test_real_zero_is_available():
    row = report([OBS])['records'][0]
    assert row['state'] == 'Available'
    assert row['raw_value'] == row['normalized_score'] == 0
    assert row['signal_weight'] == .8
    assert not row['retry_next_run']


@pytest.mark.parametrize('patch,state', [
    ({'raw_value': None}, 'Partial'),
    ({'timestamp': '2026-10-24T12:00:00Z'}, 'Stale'),
    ({'timestamp': '2026-10-26T12:00:00Z'}, 'Partial'),
    ({'timestamp': '2026-10-25T12:00:00'}, 'Partial'),
    ({'timestamp': 'bad'}, 'Partial'),
    ({'confidence': -1}, 'Partial'),
    ({'confidence': 0}, 'Partial'),
    ({'source': 'news'}, 'Partial'),
    ({'max_age_seconds': 0}, 'Partial'),
    ({'raw_value': float('nan')}, 'Partial'),
    ({'state': 'partial'}, 'Partial'),
    ({'state': 'mystery'}, 'Partial'),
    ({'state': 'error', 'raw_value': float('nan')}, 'Unavailable'),
    ({'state': 'error'}, 'Unavailable'),
    ({'state': 'timeout'}, 'Unavailable'),
])
def test_unusable_observations_never_get_signal_weight(patch, state):
    result = report([{**OBS, **patch}])
    row = result['records'][0]
    assert row['state'] == state
    assert row['signal_weight'] == 0 and not row['eligible_for_aggregation']
    assert row['retry_next_run']
    json.dumps(result, allow_nan=False)


def test_catalog_counts_and_ids_are_enforced():
    with pytest.raises(ValueError, match='factor_count'):
        build_report({**CAT, 'factor_count': 500}, [], NOW)
    with pytest.raises(ValueError, match='duplicate factor'):
        build_report({**CAT, 'factor_count': 2, 'factors': CAT['factors'] * 2}, [], NOW)
    with pytest.raises(ValueError, match='duplicate observation'):
        report([OBS, OBS])
    with pytest.raises(ValueError, match='unknown factor'):
        report([{**OBS, 'factor_id': 'F001'}])


def test_all_four_states_and_denominator():
    cat = copy.deepcopy(CAT)
    cat['factors'] = [{**CAT['factors'][0], 'id': i} for i in ('a', 'b', 'c', 'd')]
    cat['factor_count'] = 4
    observations = [{**OBS, 'factor_id': 'a'},
                    {**OBS, 'factor_id': 'b', 'raw_value': None},
                    {**OBS, 'factor_id': 'c', 'timestamp': '2000-01-01T00:00:00Z'}]
    result = build_report(cat, observations, NOW)
    assert all(n == 1 for n in result['counts'].values())
    assert result['coverage_percent'] == 25
    assert sum(result['counts'].values()) == result['factor_count']


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parents[1] / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_unhealthy_sources_have_no_primary_or_weight(tmp_path, monkeypatch):
    confidence = load_script('babimind_source_confidence')
    weights = load_script('babimind_signal_weight')
    source = tmp_path / 'health.json'
    conf = tmp_path / 'confidence.json'
    source.write_text(json.dumps({'sources': [{'name': s, 'status': s, 'topic': 'macro'} for s in ('error', 'unavailable')]}))
    monkeypatch.setattr(confidence, 'HEALTH', source)
    monkeypatch.setattr(confidence, 'OUT_JSON', conf)
    monkeypatch.setattr(confidence, 'OUT_MD', tmp_path / 'confidence.md')
    confidence.main()
    assert json.loads(conf.read_text())['routing'][0]['primary'] is None
    monkeypatch.setattr(weights, 'SRC', conf)
    monkeypatch.setattr(weights, 'OUT', tmp_path / 'weights.json')
    weights.main()
    assert all(x['signal_weight'] == 0 for x in json.loads(weights.OUT.read_text())['weights'])


def test_unmapped_rotation_source_has_zero_weight(tmp_path, monkeypatch):
    rotation = load_script('babimind_factor_rotation')
    (tmp_path / 'pipe.json').write_text('{"sources": []}')
    (tmp_path / 'cat.json').write_text(json.dumps(CAT))
    monkeypatch.setattr(rotation, 'PIPE', tmp_path / 'pipe.json')
    monkeypatch.setattr(rotation, 'FACTORS', tmp_path / 'cat.json')
    monkeypatch.setattr(rotation, 'OUT', tmp_path / 'rotation.json')
    rotation.main()
    assert json.loads(rotation.OUT.read_text())['clusters']['macro'][0]['source_weight'] == 0
