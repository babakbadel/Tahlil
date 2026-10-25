from datetime import datetime, timezone
import pytest
from scripts.validate_market_sources import validate

NOW = datetime(2030, 1, 1, 12, tzinfo=timezone.utc)


def test_async_provider_schema_is_recognized():
    assert validate({'status': 'ok', 'market_watch': [{'symbol': 'فملی'}], 'collected_at_utc': NOW.isoformat()}, NOW)['ok']


@pytest.mark.parametrize('stamp', [None, 'invalid', '2030-01-01T08:00:00Z', '2030-01-01T14:00:00Z', '2030-01-01T12:00:00'])
def test_old_or_unknown_collection_time_cannot_pass(stamp):
    assert not validate({'status': 'ok', 'rows': [{}], 'collected_at_utc': stamp}, NOW)['ok']


@pytest.mark.parametrize('body', [
    {'markets': {'bourse': {'status': 'ok', 'rows': 1, 'data': [{'symbol': 'ضملی1'}]}}},
    {'underlyings': {'فملی': {'status': 'ok', 'calls': [], 'puts': [{'symbol': 'طملی1'}]}}},
])
def test_nested_option_provider_schemas_are_recognized(body):
    assert validate({'status': 'ok', 'collected_at_utc': NOW.isoformat(), **body}, NOW)['ok']
