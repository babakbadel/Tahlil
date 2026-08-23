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
