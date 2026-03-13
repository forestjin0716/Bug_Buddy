"""
레드마인 Description 형식의 이슈 템플릿을 생성하는 모듈.

Karpathy Guideline - Simplicity First:
- 순수 f-string만 사용. 외부 템플릿 엔진(Jinja2 등) 금지.
- 단일 함수로 충분한 로직을 클래스로 감싸지 않는다.
"""

_PLACEHOLDER = "입력되지 않음"


def _val(data: dict, key: str) -> str:
    """딕셔너리에서 값을 꺼내고, 비어있으면 placeholder를 반환한다."""
    value = data.get(key, "")
    if value is None:
        return _PLACEHOLDER
    stripped = str(value).strip()
    return stripped if stripped else _PLACEHOLDER


def build_template(data: dict) -> str:
    """이슈 입력 딕셔너리를 받아 레드마인 Description 형식의 템플릿 문자열을 반환한다."""
    def _v(key): return _val(data, key)

    return f"""## 버그버디 이슈 템플릿
- Tracker: {_v('tracker')} | Status: {_v('status')} | Priority: {_v('priority')}
- 고객사: {_v('customer')} | 카테고리: {_v('category')} | 시작일: {_v('start_date')}

### (1) 에러 내용/이슈사항/문의내용
{_v('error_content')}

### (2) 메뉴명 / 페이지 정보
- 메뉴명: {_v('menu_name')}
- URL/라우트: {_v('url_route')}

### (3) 상세 키값
- 사용자 ID: {_v('user_id')}
- 문서 키/번호: {_v('doc_key')}
- 기타 키값: {_v('other_keys')}

### (4) 발생 환경/시간
- 발생일시: {_v('occurred_at')}
- 브라우저/앱: {_v('browser_info')}

### (5) 재현 절차
{_v('repro_steps')}

### (6) 기대 결과 vs 실제 결과
- 기대 결과: {_v('expected_result')}
- 실제 결과: {_v('actual_result')}

### (7) 에러 메시지/로그(원문)
{_v('error_log')}
"""
