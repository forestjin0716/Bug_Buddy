import pytest
from unittest.mock import patch, MagicMock
from src.claude_analyzer import validate_response, parse_json_response, analyze_issue


# === Validation Tests (7) ===

def test_validate_response_valid():
    data = {
        "missing_fields": ["담당자", "환경"],
        "questions_to_ask": ["담당자가 누구인가요?"],
        "redmine_subject": "[BUG] 로그인 실패",
        "redmine_description": "## 문제 설명\n로그인 시 500 에러",
        "confidence": 0.85,
        "risk_flags": []
    }
    result, err = validate_response(data)
    assert result is True and err is None


def test_validate_response_missing_key():
    data = {"missing_fields": [], "questions_to_ask": []}
    result, err = validate_response(data)
    assert result is False and "redmine_subject" in err


def test_validate_response_wrong_type_confidence():
    data = {
        "missing_fields": [],
        "questions_to_ask": [],
        "redmine_subject": "test",
        "redmine_description": "desc",
        "confidence": "high",
        "risk_flags": []
    }
    result, err = validate_response(data)
    assert result is False and "confidence" in err


def test_validate_response_confidence_out_of_range():
    data = {
        "missing_fields": [],
        "questions_to_ask": [],
        "redmine_subject": "test",
        "redmine_description": "desc",
        "confidence": 1.5,
        "risk_flags": []
    }
    result, err = validate_response(data)
    assert result is False and "confidence" in err


def test_validate_response_wrong_type_lists():
    data = {
        "missing_fields": "not a list",
        "questions_to_ask": [],
        "redmine_subject": "test",
        "redmine_description": "desc",
        "confidence": 0.5,
        "risk_flags": []
    }
    result, err = validate_response(data)
    assert result is False and "missing_fields" in err


def test_parse_json_response_valid():
    raw = '{"missing_fields":[],"questions_to_ask":[],"redmine_subject":"test","redmine_description":"desc","confidence":0.9,"risk_flags":[]}'
    result, err = parse_json_response(raw)
    assert err is None and result["confidence"] == 0.9


def test_parse_json_response_invalid():
    result, err = parse_json_response("not json")
    assert result is None and err is not None


# === Mock API Tests (3) ===

def test_analyze_issue_success():
    valid_json = '{"missing_fields":["담당자"],"questions_to_ask":["담당자가 누구인가요?"],"redmine_subject":"[BUG] 로그인 실패","redmine_description":"## 문제\\n로그인 500 에러","confidence":0.85,"risk_flags":[]}'
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=valid_json)]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message
    with patch("src.claude_analyzer.anthropic.Anthropic", return_value=mock_client):
        result, err = analyze_issue({"title": "로그인 실패", "customer": "A사"}, api_key="test-key")
    assert err is None and result["confidence"] == 0.85


def test_analyze_issue_api_error():
    import anthropic
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = anthropic.APIError(
        message="API Error", request=MagicMock(), body={}
    )
    with patch("src.claude_analyzer.anthropic.Anthropic", return_value=mock_client):
        result, err = analyze_issue({"title": "test"}, api_key="bad-key")
    assert result is None and err is not None


def test_analyze_issue_retry_on_empty_subject():
    """confidence==0.0 AND redmine_subject=="" 일 때 1회 재시도."""
    empty_json = '{"missing_fields":[],"questions_to_ask":[],"redmine_subject":"","redmine_description":"","confidence":0.0,"risk_flags":[]}'
    valid_json = '{"missing_fields":[],"questions_to_ask":[],"redmine_subject":"[BUG] 재시도 성공","redmine_description":"desc","confidence":0.7,"risk_flags":[]}'
    mock_message_empty = MagicMock()
    mock_message_empty.content = [MagicMock(text=empty_json)]
    mock_message_valid = MagicMock()
    mock_message_valid.content = [MagicMock(text=valid_json)]
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [mock_message_empty, mock_message_valid]
    with patch("src.claude_analyzer.anthropic.Anthropic", return_value=mock_client):
        result, err = analyze_issue({"title": "test"}, api_key="test-key")
    assert mock_client.messages.create.call_count == 2
    assert result["redmine_subject"] == "[BUG] 재시도 성공"
