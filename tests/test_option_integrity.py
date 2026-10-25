import csv
from dataclasses import replace
from datetime import date

import pytest

from app.options.ranking import OptionContract, rank_options
from scripts import ingest_option_market_watch as ingest


def contract(**changes):
    base = OptionContract('ضملی1', 'فملی', 'call', 100, date(2030, 2, 1),
                          last_price=10, bid=9, ask=11, volume=100, open_interest=200,
                          event_time='2030-01-01T09:00:00+03:30', underlying_price=105,
                          underlying_event_time='2030-01-01T09:00:00+03:30')
    return replace(base, **changes)


def test_csv_keeps_call_and_put_direction(tmp_path, monkeypatch):
    source = tmp_path / 'options.csv'
    rows = []
    for symbol in ('ضملی1', 'طملی1'):
        row = ['0'] * 43
        row[0], row[20] = symbol, 'فملی'
        rows.append(row)
    with source.open('w', encoding='utf-8', newline='') as handle:
        csv.writer(handle).writerows([['header'] * 43, *rows])
    monkeypatch.setattr(ingest, 'SOURCE', source)
    assert [r['option_type'] for r in ingest.parse_rows()] == ['call', 'put']


@pytest.mark.parametrize('changes', [
    {'strike': 0}, {'strike': float('nan')}, {'option_type': 'invalid'},
    {'last_price': None}, {'last_price': -1}, {'volume': -1},
    {'bid': 12, 'ask': 11}, {'underlying_price': None},
    {'event_time': '2030-01-01T12:00:00+03:30'},
    {'event_time': 'bad timestamp'}, {'event_time': '2030-01-02T09:00:00+03:30'},
])
def test_invalid_or_unsynchronized_quotes_cannot_get_final_rank(changes):
    result = rank_options([contract(**changes)], '2030-01-01')[0]
    assert result.rank is None
    assert result.score is None


def test_missing_premium_does_not_become_zero():
    assert rank_options([contract(last_price=None)], '2030-01-01')[0].break_even is None


def test_expiry_gate_and_valid_ranking():
    assert rank_options([contract(expiry=date(2030, 1, 1))], '2030-01-01') == []
    assert rank_options([contract()], '2030-01-01')[0].rank == 1


def test_optional_sync_gate_can_be_disabled_explicitly():
    assert rank_options([contract(event_time=None)], '2030-01-01', require_synchronized=False)[0].rank == 1


def test_synchronized_historical_quotes_are_not_current_quotes():
    result = rank_options([contract(event_time='2029-12-31T09:00:00+03:30', underlying_event_time='2029-12-31T09:00:00+03:30')], '2030-01-01')[0]
    assert result.rank is None
    assert 'stale_quote' in result.data_gaps
