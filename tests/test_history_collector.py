from scripts import collect_brs_history as collector
from app.data.brsapi.client import BrsApiClient


def test_history_client_requests_adjusted_daily_type(monkeypatch):
    client = BrsApiClient(api_key='test-only')
    requests = []
    monkeypatch.setattr(client, '_get_json', lambda endpoint, **params: requests.append((endpoint, params)))
    client.get_daily_history('فملی')
    assert requests == [('Candlestick.php', {'type': 3, 'l18': 'فملی'})]


def test_history_collector_does_not_accept_intraday_or_wrong_symbol(monkeypatch):
    class Client:
        def __init__(self, **kwargs): pass
        def get_daily_history(self, symbol):
            return {'l18': symbol, 'type': 1, 'candle_daily_adjusted': [{'date': '1405-08-04', 'close': 100}]}
    monkeypatch.setattr(collector, 'BrsApiClient', Client)
    _, result = collector.collect('فملی')
    assert result['status'] == 'unavailable'
    assert result['records'] == []


def test_history_errors_cannot_serialize_secrets(monkeypatch):
    class Client:
        def __init__(self, **kwargs): pass
        def get_daily_history(self, symbol):
            raise RuntimeError('secret-test-key')
    monkeypatch.setattr(collector, 'BrsApiClient', Client)
    _, result = collector.collect('فملی')
    assert 'secret-test-key' not in str(result)
    assert result['error_type'] == 'RuntimeError'
