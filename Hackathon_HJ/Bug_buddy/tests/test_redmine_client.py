import pytest
from unittest.mock import patch, MagicMock
from src.redmine_client import get_trackers, get_issue_statuses, load_trackers_with_fallback, load_statuses_with_fallback, TRACKER_FALLBACK, STATUS_FALLBACK


def test_get_trackers_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"trackers": [{"id": 1, "name": "Defect"}, {"id": 2, "name": "Feature"}]}
    with patch("src.redmine_client.requests.get", return_value=mock_response):
        result, err = get_trackers("http://redmine.internal", "api_key_123")
    assert err is None and len(result) == 2 and result[0]["name"] == "Defect"


def test_get_trackers_auth_failure():
    mock_response = MagicMock()
    mock_response.status_code = 401
    with patch("src.redmine_client.requests.get", return_value=mock_response):
        result, err = get_trackers("http://redmine.internal", "bad_key")
    assert result is None and "인증" in err


def test_get_trackers_connection_error():
    import requests
    with patch("src.redmine_client.requests.get", side_effect=requests.ConnectionError()):
        result, err = get_trackers("http://redmine.internal", "key")
    assert result is None and err is not None


def test_get_trackers_timeout():
    import requests
    with patch("src.redmine_client.requests.get", side_effect=requests.Timeout()):
        result, err = get_trackers("http://redmine.internal", "key")
    assert result is None and "타임아웃" in err


def test_get_issue_statuses_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"issue_statuses": [{"id": 1, "name": "New"}, {"id": 2, "name": "In progress"}]}
    with patch("src.redmine_client.requests.get", return_value=mock_response):
        result, err = get_issue_statuses("http://redmine.internal", "key")
    assert err is None and result[0]["name"] == "New"


def test_get_trackers_missing_env():
    result, err = get_trackers("", "")
    assert result is None and err is not None


def test_fallback_trackers():
    names = load_trackers_with_fallback("", "")
    assert isinstance(names, list) and len(names) > 0
    assert names == TRACKER_FALLBACK


def test_fallback_statuses():
    names = load_statuses_with_fallback("", "")
    assert isinstance(names, list) and len(names) > 0
    assert names == STATUS_FALLBACK


def test_fallback_uses_api_when_available():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"trackers": [{"id": 1, "name": "Custom"}]}
    with patch("src.redmine_client.requests.get", return_value=mock_response):
        names = load_trackers_with_fallback("http://redmine.internal", "valid_key")
    assert names == ["Custom"]
