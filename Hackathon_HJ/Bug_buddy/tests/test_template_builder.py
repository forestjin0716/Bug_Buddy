"""
src/template_builder.py의 build_template 함수 단위 테스트.
TDD 방식: 구현 전에 먼저 작성하여 실패 확인 후 구현.
"""
import pytest
from src.template_builder import build_template


@pytest.fixture
def full_input():
    return {
        "tracker": "Defect",
        "status": "New",
        "start_date": "2026-03-20",
        "priority": "높음",
        "category": "SFE",
        "customer": "종근당",
        "menu_name": "주문관리",
        "url_route": "/biz/ord/list",
        "user_id": "user_001",
        "doc_key": "ORD-20260320-001",
        "other_keys": "session_id=abc123",
        "occurred_at": "2026-03-20 14:30",
        "browser_info": "Chrome 122, Windows 11",
        "error_content": "주문 목록 조회 시 500 에러 발생",
        "repro_steps": "1. 주문관리 메뉴 진입\n2. 목록 조회 클릭\n3. 500 에러 화면 표시",
        "expected_result": "주문 목록이 정상 표시되어야 함",
        "actual_result": "500 Internal Server Error 화면 표시",
        "error_log": "ERROR 2026-03-20 14:30:00 NullPointerException at OrderService.java:142",
    }


@pytest.fixture
def empty_input():
    return {
        "tracker": "Defect",
        "status": "New",
        "start_date": "2026-03-20",
        "priority": "보통",
        "category": "SFE",
        "customer": "대웅제약",
        "menu_name": "",
        "url_route": "",
        "user_id": "",
        "doc_key": "",
        "other_keys": "",
        "occurred_at": "",
        "browser_info": "",
        "error_content": "로그인 후 메인 화면이 안 보임",
        "repro_steps": "",
        "expected_result": "",
        "actual_result": "",
        "error_log": "",
    }


def test_returns_string(full_input):
    result = build_template(full_input)
    assert isinstance(result, str)


def test_has_all_seven_sections(full_input):
    result = build_template(full_input)
    assert "(1) 에러 내용/이슈사항/문의내용" in result
    assert "(2) 메뉴명 / 페이지 정보" in result
    assert "(3) 상세 키값" in result
    assert "(4) 발생 환경/시간" in result
    assert "(5) 재현 절차" in result
    assert "(6) 기대 결과 vs 실제 결과" in result
    assert "(7) 에러 메시지/로그(원문)" in result


def test_filled_field_appears_in_output(full_input):
    result = build_template(full_input)
    assert "주문 목록 조회 시 500 에러 발생" in result
    assert "주문관리" in result
    assert "/biz/ord/list" in result
    assert "user_001" in result
    assert "ORD-20260320-001" in result


def test_empty_field_shows_placeholder(empty_input):
    result = build_template(empty_input)
    assert result.count("입력되지 않음") >= 6


def test_section_1_contains_error_content(full_input):
    result = build_template(full_input)
    section_1_start = result.index("(1) 에러 내용/이슈사항/문의내용")
    section_2_start = result.index("(2) 메뉴명 / 페이지 정보")
    section_1_content = result[section_1_start:section_2_start]
    assert "주문 목록 조회 시 500 에러 발생" in section_1_content


def test_section_5_contains_steps(full_input):
    result = build_template(full_input)
    section_5_start = result.index("(5) 재현 절차")
    section_6_start = result.index("(6) 기대 결과 vs 실제 결과")
    section_5_content = result[section_5_start:section_6_start]
    assert "1. 주문관리 메뉴 진입" in section_5_content


def test_special_chars_handled():
    special_input = {
        "tracker": "Defect",
        "status": "New",
        "start_date": "2026-03-20",
        "priority": "즉시",
        "category": "주문,반품,수금",
        "customer": "대웅제약",
        "menu_name": "주문/반품 처리",
        "url_route": "/api/v1/order?status=FAIL&code=500",
        "user_id": "user@company.com",
        "doc_key": "",
        "other_keys": 'key="value with spaces"',
        "occurred_at": "",
        "browser_info": "",
        "error_content": "에러 발생!\n줄바꿈 포함\n탭\t포함",
        "repro_steps": "1. 진입\n2. 클릭\n3. 에러",
        "expected_result": "",
        "actual_result": "",
        "error_log": '{"error": "NullPointerException", "code": 500}',
    }
    result = build_template(special_input)
    assert isinstance(result, str)
    assert "주문/반품 처리" in result
    assert "에러 발생!" in result
    assert '{"error": "NullPointerException"' in result


def test_newlines_preserved(full_input):
    result = build_template(full_input)
    assert "1. 주문관리 메뉴 진입" in result
    assert "2. 목록 조회 클릭" in result


def test_metadata_in_output(full_input):
    result = build_template(full_input)
    assert "Defect" in result
    assert "높음" in result
    assert "종근당" in result
    assert "SFE" in result
