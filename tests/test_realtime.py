from app.data.brsapi.realtime import normalize


def test_normalize_splits_equity_and_option():
    rows = [
        {"l18": "فملی", "pl": 12500},
        {"l18": "ضملی7070", "base_l18": "فملی", "pl": 500},
    ]
    result = normalize(rows)
    assert result["schema_version"] == "1.0"
    assert result["data"]["equity_count"] == 1
    assert result["data"]["option_count"] == 1


def test_normalize_empty_feed_is_partial():
    result = normalize([])
    assert result["data_quality"]["status"] == "partial"
    assert result["data"]["equity_count"] == 0


def test_collector_uses_dedicated_options_feed():
    from app.data.brsapi.realtime import RealtimeCollector

    class Client:
        def get_all_symbols(self, security_type):
            return [{'l18': 'فملی'}]

        def get_options(self):
            return [{'l18': 'ضملی1', 'base_l18': 'فملی'}]

    result = RealtimeCollector(client=Client()).collect_once()
    assert result['data']['option_count'] == 1
    assert result['data_quality']['status'] == 'live'


async def test_polling_does_not_block_event_loop_and_survives_transport_error():
    import asyncio
    import threading
    import requests
    from app.data.brsapi.realtime import RealtimeCollector
    from app.data.brsapi.stream import RealtimeHub

    started, release = threading.Event(), threading.Event()

    class Client:
        def get_all_symbols(self, security_type):
            started.set()
            release.wait(timeout=2)
            raise requests.ConnectionError('provider unavailable')

    collector = RealtimeCollector(client=Client(), hub=RealtimeHub())
    task = asyncio.create_task(collector.run_forever())
    try:
        for _ in range(100):
            if started.is_set():
                break
            await asyncio.sleep(.005)
        assert started.is_set()
        assert not release.is_set()
        release.set()
        await asyncio.sleep(.05)
        assert not task.done()
        assert collector.last_error == 'ConnectionError'
    finally:
        release.set()
        collector.stop()
        task.cancel()
        with __import__('contextlib').suppress(asyncio.CancelledError):
            await task


def test_api_import_and_health_work_without_credentials(monkeypatch):
    from fastapi.testclient import TestClient
    import realtime_api
    monkeypatch.setattr(realtime_api.collector, 'latest', None)
    monkeypatch.setattr(realtime_api.collector, 'last_error', None)
    client = TestClient(realtime_api.app)
    assert client.get('/health').status_code == 200
    monkeypatch.setattr(realtime_api.collector.client, 'api_key', None)
    assert client.get('/api/v1/market/realtime').status_code == 503


def test_transport_exception_does_not_expose_api_key(monkeypatch):
    import requests
    import traceback
    from app.data.brsapi.client import BrsApiClient, BrsApiError
    client = BrsApiClient(api_key='private-test-key')

    def fail(*args, **kwargs):
        raise requests.ConnectionError('https://provider.invalid/?key=private-test-key')

    monkeypatch.setattr(client.session, 'get', fail)
    try:
        client.get_options()
    except BrsApiError:
        assert 'private-test-key' not in traceback.format_exc()
    else:
        raise AssertionError('Expected a sanitized API error')
