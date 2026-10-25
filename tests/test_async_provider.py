import asyncio
import json
import sys
from types import ModuleType
from scripts import collect_tsetmc_async as collector


def test_optional_import_failure_is_persisted(tmp_path, monkeypatch):
    out = tmp_path / 'snapshot.json'
    monkeypatch.setattr(collector, 'OUT', out)
    monkeypatch.setitem(sys.modules, 'tsetmc.market_watch', None)
    assert collector.main() == 1
    payload = json.loads(out.read_text())
    assert payload['status'] == 'error'
    assert 'ModuleNotFoundError' in payload['error']


def test_auxiliary_feed_failure_preserves_valid_market_rows(monkeypatch):
    parent, market = ModuleType('tsetmc'), ModuleType('tsetmc.market_watch')
    parent.__path__ = []

    class Frame:
        def to_dicts(self):
            return [{'symbol': 'فملی'}]

    async def prices(**kwargs):
        return Frame()

    async def failed():
        raise TimeoutError()

    market.get_market_watch = prices
    market.client_type_all = failed
    market.closing_price_all = failed
    monkeypatch.setitem(sys.modules, 'tsetmc', parent)
    monkeypatch.setitem(sys.modules, 'tsetmc.market_watch', market)
    payload = asyncio.run(collector.collect())
    assert payload['status'] == 'ok'
    assert len(payload['market_watch']) == 1
    assert payload['client_type_all'] == []
    assert payload['errors'] == {'client_type_all': 'TimeoutError', 'closing_price_all': 'TimeoutError'}
