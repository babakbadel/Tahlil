import json
import pandas as pd
from scripts import babimind_graph as graph
from scripts import babimind_memory as memory
from scripts.collect_kamandar_market_sections import normalize_url
from scripts.collect_kamandar_services import canonical
from app.data.finpy_tse_adapter import _records


def test_persian_market_links_are_encoded_once():
    raw = 'https://kamandar.ir/app/market/فملی?q=خرید'
    for normalize in (lambda url: normalize_url('https://kamandar.ir', url), canonical):
        encoded = normalize(raw)
        assert encoded.isascii()
        assert '%D9' in encoded
        assert normalize(encoded) == encoded


def test_code_graph_cannot_become_a_bullish_signal(tmp_path, monkeypatch):
    source, out = tmp_path / 'graph.json', tmp_path / 'result.json'
    source.write_text(json.dumps({'edges': [{'source': 'USD', 'target': 'فملی', 'direction': 1, 'weight': 1}]}))
    monkeypatch.setattr(graph, 'GRAPH', source)
    monkeypatch.setattr(graph, 'OUT', out)
    graph.main()
    payload = json.loads(out.read_text())
    assert payload['index_edge_count'] == 1
    assert payload['graph_score'] is None
    assert payload['market_signal_eligible'] is False


def test_heading_based_llm_output_is_archived_without_losing_content(tmp_path, monkeypatch):
    monkeypatch.setattr(memory, 'ROOT', tmp_path)
    result = {'generated_at': '2030-01-01', 'analysis': {'Market regime': 'uncertain', 'Scenarios': {'bullish': .2, 'neutral': .5, 'bearish': .3}, 'Decision': 'WAIT', 'Safety / integrity': 'data gaps'}}
    row = memory.compact(result)
    assert row['regime'] == 'uncertain'
    assert row['market_implications'] == 'WAIT'
    memory.archive_full(result, row)
    memory.archive_full(result, row)
    lines = (tmp_path / 'data/model_llm_history.jsonl').read_text().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])['result'] == result


def test_finpy_price_dates_are_not_lost_in_index():
    frame = pd.DataFrame({'Adj Close': [100]}, index=pd.Index(['1405-08-04'], name='J-Date'))
    assert _records(frame)[0]['J-Date'] == '1405-08-04'
