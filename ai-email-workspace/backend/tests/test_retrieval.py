from app.services.chat import _parse_filters


def test_parse_filters():
    query, filters = _parse_filters("from:alice subject:Update before:2024-01-01 status")
    assert query == "status"
    assert filters["from"] == "alice"
    assert filters["subject"] == "Update"
    assert filters["before"] == "2024-01-01"
