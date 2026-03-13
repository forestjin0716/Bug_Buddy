# Sprint 1: 이슈 입력 폼 + 레드마인 Description 템플릿 생성 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** "버그버디에게 정리 부탁하기" 버튼 클릭 시 레드마인 Description 형식의 7개 섹션 템플릿이 생성되어 복사할 수 있다.

**Architecture:** `src/template_builder.py`에 순수 f-string 기반 템플릿 생성 함수를 구현하고, `app.py`의 좌측 컬럼에 `st.form`을 배치하며, 우측 컬럼에 `st.code`로 결과를 표시한다. 외부 템플릿 엔진(Jinja2 등) 일절 사용하지 않는 입력 → 문자열 조합 → 출력의 직선적 흐름을 따른다.

**Tech Stack:** Python 3.x, Streamlit, pytest

---

## Karpathy Guideline: Simplicity First

- 순수 f-string만 사용. Jinja2 등 외부 템플릿 엔진 도입 금지.
- 단일 함수로 충분한 로직을 클래스로 감싸지 않는다.
- 입력 딕셔너리 → 문자열 조합 → 반환의 직선적 흐름.

---

### Task 1: template_builder 실패 테스트 작성 (TDD 선행)

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_template_builder.py`

**Step 1: tests 디렉터리 및 `__init__.py` 생성** (2분)

```bash
mkdir -p tests
touch tests/__init__.py
```

**Step 2: 실패 테스트 작성** (5분)

`tests/test_template_builder.py`를 아래 내용으로 생성한다:

```python
"""
src/template_builder.py의 build_template 함수 단위 테스트.
TDD 방식: 구현 전에 먼저 작성하여 실패 확인 후 구현.
"""
import pytest
from src.template_builder import build_template


# --- 테스트용 픽스처 ---

@pytest.fixture
def full_input():
    """모든 필드가 채워진 완전한 입력 딕셔너리."""
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
    """선택 필드가 모두 비어있는 최소 입력 (error_content만 필수)."""
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


# --- 테스트 케이스 ---

def test_returns_string(full_input):
    """반환값이 문자열이어야 한다."""
    result = build_template(full_input)
    assert isinstance(result, str)


def test_has_all_seven_sections(full_input):
    """7개 섹션 헤더가 모두 포함되어야 한다."""
    result = build_template(full_input)
    assert "(1) 에러 내용/이슈사항/문의내용" in result
    assert "(2) 메뉴명 / 페이지 정보" in result
    assert "(3) 상세 키값" in result
    assert "(4) 발생 환경/시간" in result
    assert "(5) 재현 절차" in result
    assert "(6) 기대 결과 vs 실제 결과" in result
    assert "(7) 에러 메시지/로그(원문)" in result


def test_filled_field_appears_in_output(full_input):
    """입력된 값이 출력 템플릿에 포함되어야 한다."""
    result = build_template(full_input)
    assert "주문 목록 조회 시 500 에러 발생" in result
    assert "주문관리" in result
    assert "/biz/ord/list" in result
    assert "user_001" in result
    assert "ORD-20260320-001" in result


def test_empty_field_shows_placeholder(empty_input):
    """빈 선택 필드는 '입력되지 않음' placeholder로 채워져야 한다."""
    result = build_template(empty_input)
    assert result.count("입력되지 않음") >= 6


def test_section_1_contains_error_content(full_input):
    """에러 내용이 섹션 (1) 안에 위치해야 한다."""
    result = build_template(full_input)
    section_1_start = result.index("(1) 에러 내용/이슈사항/문의내용")
    section_2_start = result.index("(2) 메뉴명 / 페이지 정보")
    section_1_content = result[section_1_start:section_2_start]
    assert "주문 목록 조회 시 500 에러 발생" in section_1_content


def test_section_5_contains_steps(full_input):
    """재현 절차 내용이 섹션 (5) 안에 위치해야 한다."""
    result = build_template(full_input)
    section_5_start = result.index("(5) 재현 절차")
    section_6_start = result.index("(6) 기대 결과 vs 실제 결과")
    section_5_content = result[section_5_start:section_6_start]
    assert "1. 주문관리 메뉴 진입" in section_5_content


def test_special_chars_handled():
    """특수문자와 줄바꿈이 포함된 입력도 정상 처리되어야 한다."""
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
    """재현 절차의 줄바꿈이 출력에 보존되어야 한다."""
    result = build_template(full_input)
    assert "1. 주문관리 메뉴 진입" in result
    assert "2. 목록 조회 클릭" in result


def test_metadata_in_output(full_input):
    """메타데이터(Tracker, Priority, 고객사 등)가 출력에 포함되어야 한다."""
    result = build_template(full_input)
    assert "Defect" in result
    assert "높음" in result
    assert "종근당" in result
    assert "SFE" in result
```

**Step 3: 실패 확인** (2분)

Run: `pytest tests/test_template_builder.py -v`

Expected: `ModuleNotFoundError: No module named 'src.template_builder'` 또는 9개 FAILED

```
FAILED tests/test_template_builder.py::test_returns_string
FAILED tests/test_template_builder.py::test_has_all_seven_sections
...
9 failed
```

**Step 4: Commit** (2분)

```bash
git add tests/__init__.py tests/test_template_builder.py
git commit -m "test: add 9 failing unit tests for build_template (TDD)"
```

---

### Task 2: template_builder 최소 구현

**Files:**
- Create: `src/__init__.py` (없으면)
- Create: `src/template_builder.py`

**Step 1: src 디렉터리 및 `__init__.py` 확인** (2분)

```bash
mkdir -p src
touch src/__init__.py
```

**Step 2: 최소 구현 작성** (5분)

`src/template_builder.py`:

```python
"""
레드마인 Description 형식의 이슈 템플릿을 생성하는 모듈.

Karpathy Guideline - Simplicity First:
- 순수 f-string만 사용. 외부 템플릿 엔진(Jinja2 등) 금지.
- 단일 함수로 충분한 로직을 클래스로 감싸지 않는다.
- 입력 딕셔너리 → 문자열 조합 → 반환의 직선적 흐름.
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
    """이슈 입력 딕셔너리를 받아 레드마인 Description 형식의 템플릿 문자열을 반환한다.

    Args:
        data: 입력 딕셔너리. 키 목록:
            tracker, status, start_date, priority, category, customer,
            menu_name, url_route, user_id, doc_key, other_keys,
            occurred_at, browser_info, error_content, repro_steps,
            expected_result, actual_result, error_log

    Returns:
        레드마인 Description 형식의 문자열
    """
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
```

**Step 3: 통과 확인** (2분)

Run: `pytest tests/test_template_builder.py -v`

Expected:
```
tests/test_template_builder.py::test_returns_string PASSED
tests/test_template_builder.py::test_has_all_seven_sections PASSED
tests/test_template_builder.py::test_filled_field_appears_in_output PASSED
tests/test_template_builder.py::test_empty_field_shows_placeholder PASSED
tests/test_template_builder.py::test_section_1_contains_error_content PASSED
tests/test_template_builder.py::test_section_5_contains_steps PASSED
tests/test_template_builder.py::test_special_chars_handled PASSED
tests/test_template_builder.py::test_newlines_preserved PASSED
tests/test_template_builder.py::test_metadata_in_output PASSED

9 passed in X.XXs
```

**Step 4: Commit** (2분)

```bash
git add src/__init__.py src/template_builder.py
git commit -m "feat: implement build_template with pure f-string formatting"
```

---

### Task 3: 메타데이터 입력 폼 UI

**Files:**
- Modify: `app.py`

**Step 1: 상수 블록 추가** (3분)

`app.py` 상단 import 영역 아래에 아래 상수 블록이 없으면 추가한다:

```python
import datetime
from src.template_builder import build_template

# --- 이슈 입력 폼 상수 ---
# Phase 4에서 Redmine API 응답으로 교체 예정
TRACKERS = ["Common", "Feature", "Defect", "Request", "Patch", "Issue", "Review"]
STATUSES = ["New", "Confirm", "Assigned", "In progress", "Resolved", "Closed", "Need Feedback", "Rejected"]
PRIORITIES = ["낮음", "보통", "높음", "즉시"]
CATEGORIES = ["SFE", "주문,반품,수금", "지출보고"]

# Phase 3에서 customers.json 기반으로 교체 예정
CUSTOMERS = [
    "웹취약점 개선", "DNC", "FMC", "넥스팜", "다케다", "대웅바이오", "대웅제약",
    "동구바이오", "메드트로닉", "박스터", "벡톤디킨스코리아", "보령컨슈머헬스케어",
    "삼일제약", "성보화학", "시지바이오", "신풍제약", "종근당", "캔논메디칼시스템즈",
    "한국다이이찌산쿄", "한국아스텔라스", "한국코와", "한독", "한옥바이오", "휴온스",
]
```

**Step 2: 좌측 컬럼 내 메타데이터 폼 구현** (5분)

`app.py`에서 좌측 컬럼 영역(기존 placeholder 위치)에 아래 코드를 추가한다:

```python
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("이슈 작성")

    with st.form(key="issue_form"):
        # --- 메타데이터 영역 ---
        st.markdown("#### 기본 정보")

        tracker = st.selectbox(
            "Tracker",
            options=TRACKERS,
            index=TRACKERS.index("Defect"),
        )
        status = st.selectbox(
            "Status",
            options=STATUSES,
            index=STATUSES.index("New"),
        )
        start_date = st.date_input(
            "Start date",
            value=datetime.date.today(),
        )
        priority = st.selectbox(
            "Priority",
            options=PRIORITIES,
            index=PRIORITIES.index("보통"),
        )
        category = st.selectbox(
            "Category",
            options=CATEGORIES,
        )
        customer = st.selectbox(
            "고객사",
            options=CUSTOMERS,
        )
```

**Step 3: 앱 실행 확인** (3분)

Run: `streamlit run app.py`

브라우저 `http://localhost:8501` 에서:
- Tracker/Status/Priority/Category/고객사 드롭다운이 좌측에 렌더링되는지 확인
- 고객사 드롭다운에 24개 항목이 모두 표시되는지 확인
- Start date에 오늘 날짜가 기본값으로 설정되는지 확인

**Step 4: Commit** (2분)

```bash
git add app.py
git commit -m "feat: add metadata form section with tracker/status/priority/category/customer dropdowns"
```

---

### Task 4: 상세 정보 + 본문 입력 폼

**Files:**
- Modify: `app.py` (Task 3의 `st.form` 블록 내부에 이어서 추가)

**Step 1: 상세 정보 필드 추가** (5분)

Task 3의 `customer = st.selectbox(...)` 바로 아래에 이어서 작성한다:

```python
        # --- 상세 정보 영역 ---
        st.markdown("---")
        st.markdown("#### 상세 정보 (선택)")

        menu_name = st.text_input(
            "메뉴명",
            placeholder="예: 주문관리, 반품처리",
        )
        url_route = st.text_input(
            "URL/라우트 (알면)",
            placeholder="예: /biz/ord/list",
        )
        user_id = st.text_input(
            "사용자 ID",
            placeholder="예: user_001 (이름/주민번호 입력 금지)",
        )
        doc_key = st.text_input(
            "문서 키/번호",
            placeholder="예: ORD-20260320-001",
        )
        other_keys = st.text_input(
            "기타 키값",
            placeholder="예: session_id=abc123",
        )
        occurred_at = st.text_input(
            "발생일시 (알면)",
            placeholder="예: 2026-03-20 14:30",
        )
        browser_info = st.text_input(
            "브라우저/앱 정보 (알면)",
            placeholder="예: Chrome 122, Windows 11",
        )
```

**Step 2: 본문 영역 및 PII 경고 + 제출 버튼 추가** (5분)

`browser_info = st.text_input(...)` 바로 아래에 이어서 작성한다:

```python
        # --- 본문 영역 ---
        st.markdown("---")
        st.markdown("#### 이슈 내용")

        st.info("🔒 환자명/주민번호 등은 올리지 말아 주세요. 내부 ID로만 적어 주세요.")

        error_content = st.text_area(
            "에러 내용/이슈사항/문의내용",
            placeholder="어떤 문제가 발생했는지 자세히 적어 주세요.",
            height=120,
        )
        repro_steps = st.text_area(
            "재현 절차",
            placeholder="1. 메뉴 진입\n2. 버튼 클릭\n3. 에러 발생",
            height=100,
        )
        expected_result = st.text_area(
            "기대 결과",
            placeholder="정상 동작 시 어떤 화면이 보여야 하나요?",
            height=80,
        )
        actual_result = st.text_area(
            "실제 결과",
            placeholder="실제로 어떤 화면/동작이 나타났나요?",
            height=80,
        )
        error_log = st.text_area(
            "에러 메시지/로그 (원문)",
            placeholder="에러 팝업 문구 또는 콘솔 로그를 그대로 붙여넣어 주세요.",
            height=100,
        )

        # --- 제출 버튼 ---
        submitted = st.form_submit_button(
            "🐛 버그버디에게 정리 부탁하기",
            type="primary",
            use_container_width=True,
        )
```

**Step 3: 앱 실행 확인** (3분)

Run: `streamlit run app.py`

브라우저에서:
- PII 경고 안내문(파란색 info 박스)이 표시되는지 확인
- 에러 내용, 재현 절차, 기대 결과, 실제 결과, 에러 로그 `text_area` 필드가 표시되는지 확인
- "🐛 버그버디에게 정리 부탁하기" 버튼이 파란색 Primary 스타일로 표시되는지 확인

**Step 4: Commit** (2분)

```bash
git add app.py
git commit -m "feat: add detail fields, body text areas, PII warning, and submit button"
```

---

### Task 5: 템플릿 생성 결과 표시

**Files:**
- Modify: `app.py` (우측 컬럼 영역 추가)

**Step 1: 우측 컬럼 결과 표시 로직 구현** (5분)

`col_left` 블록이 끝난 뒤 `col_right` 블록에 아래 코드를 추가한다:

```python
with col_right:
    st.subheader("버그버디 결과")

    if submitted:
        # 필수 필드 검증
        if not error_content.strip():
            st.warning("무슨 일이 있었는지 알려주세요!")
        else:
            form_data = {
                "tracker": tracker,
                "status": status,
                "start_date": str(start_date),
                "priority": priority,
                "category": category,
                "customer": customer,
                "menu_name": menu_name,
                "url_route": url_route,
                "user_id": user_id,
                "doc_key": doc_key,
                "other_keys": other_keys,
                "occurred_at": occurred_at,
                "browser_info": browser_info,
                "error_content": error_content,
                "repro_steps": repro_steps,
                "expected_result": expected_result,
                "actual_result": actual_result,
                "error_log": error_log,
            }

            template_text = build_template(form_data)

            st.success("템플릿이 생성됐어요! 아래 내용을 레드마인에 붙여넣어 주세요.")
            st.subheader("📋 레드마인 Description 템플릿")
            # st.code는 우측 상단에 복사 아이콘을 내장 제공
            st.code(template_text, language="markdown")
    else:
        st.markdown(
            "왼쪽에서 이슈 정보를 입력하고\n"
            "**🐛 버그버디에게 정리 부탁하기** 버튼을 눌러 주세요."
        )
```

**Step 2: 앱 전체 흐름 수동 확인** (5분)

Run: `streamlit run app.py`

아래 순서로 브라우저(`http://localhost:8501`)에서 확인한다:

1. 에러 내용 비워두고 버튼 클릭 → "무슨 일이 있었는지 알려주세요!" 경고 확인
2. Tracker="Defect", Priority="높음", 고객사="종근당", 메뉴명="주문관리", 에러 내용="주문 목록 조회 시 500 에러 발생" 입력 후 버튼 클릭
3. 우측에 7개 섹션 템플릿 출력 확인
4. 빈 필드에 "입력되지 않음" 표시 확인
5. `st.code` 블록 우측 상단 복사 아이콘 클릭 → 클립보드 복사 확인

**Step 3: 전체 단위 테스트 회귀 확인** (2분)

Run: `pytest tests/test_template_builder.py -v`

Expected: `9 passed`

**Step 4: Commit** (2분)

```bash
git add app.py
git commit -m "feat: add template generation button handler and result display in right column"
```

---

### Task 6: 통합 수동 검증 (Playwright MCP 3개 시나리오)

**Files:**
- 없음 (수동 검증 + Playwright MCP 실행)

**Step 1: 앱 실행** (2분)

```bash
streamlit run app.py
```

Expected: `http://localhost:8501` 정상 접속

**Step 2: Playwright MCP - 시나리오 1: 렌더링 검증** (3분)

```
1. browser_navigate → http://localhost:8501
2. browser_snapshot → Tracker/Status/Priority/Category 드롭다운 존재 확인
3. browser_snapshot → 고객사 드롭다운 24개 항목 확인
4. browser_select_option → 고객사 드롭다운에서 "대웅제약" 선택
5. browser_snapshot → "대웅제약" 선택 반영 확인
6. browser_snapshot → PII 경고 "환자명/주민번호 등은 올리지 말아 주세요" 표시 확인
```

Expected: 드롭다운 24개 항목 모두 노출, PII 경고 표시

**Step 3: Playwright MCP - 시나리오 2: 템플릿 생성 정상 흐름** (5분)

```
1. browser_select_option → Tracker = "Defect"
2. browser_select_option → Priority = "높음"
3. browser_select_option → 고객사 = "종근당"
4. browser_type → 메뉴명 필드에 "주문관리" 입력
5. browser_type → 에러 내용 필드에 "주문 목록 조회 시 500 에러 발생" 입력
6. browser_click → "🐛 버그버디에게 정리 부탁하기" 버튼 클릭
7. browser_wait_for → 우측 영역에 "(1) 에러 내용" 텍스트 대기
8. browser_snapshot → 7개 섹션 구조 확인
9. browser_snapshot → 미입력 필드에 "입력되지 않음" 표시 확인
10. browser_console_messages(level: "error") → 콘솔 에러 없음 확인
```

Expected: 7개 섹션 포함 템플릿 출력, 콘솔 에러 0개

**Step 4: Playwright MCP - 시나리오 3: 빈 입력 검증** (3분)

```
1. browser_navigate → http://localhost:8501
2. browser_click → "🐛 버그버디에게 정리 부탁하기" 버튼 클릭
3. browser_wait_for → "무슨 일이 있었는지 알려주세요!" 메시지 대기
4. browser_snapshot → 경고 메시지 확인
```

Expected: 경고 메시지 표시, 템플릿 생성 안 됨

**Step 5: 최종 Commit** (2분)

```bash
git add .
git commit -m "chore: sprint 1 manual and playwright validation complete"
```

---

## 완료 기준 (Definition of Done)

- [ ] 모든 입력 필드가 Streamlit UI에 렌더링됨
- [ ] 24개 고객사가 드롭다운에 모두 표시됨
- [ ] "🐛 버그버디에게 정리 부탁하기" 클릭 시 7개 섹션 템플릿이 우측에 표시됨
- [ ] 빈 선택 필드는 `입력되지 않음`으로 채워짐
- [ ] `st.code` 내장 복사 아이콘으로 클립보드 복사 가능
- [ ] PII 경고 안내문이 입력 영역에 표시됨
- [ ] 에러 내용 빈 값 시 "무슨 일이 있었는지 알려주세요!" 경고 표시
- [ ] `pytest tests/test_template_builder.py` 9개 테스트 전체 통과

---

## 예상 산출물

| 파일 | 상태 | 설명 |
|------|------|------|
| `src/template_builder.py` | 신규 | 순수 f-string 기반 템플릿 생성 함수 |
| `tests/test_template_builder.py` | 신규 | 9개 단위 테스트 (TDD) |
| `tests/__init__.py` | 신규 (없으면) | 테스트 패키지 초기화 |
| `src/__init__.py` | 신규 (없으면) | src 패키지 초기화 |
| `app.py` | 수정 | 이슈 입력 폼 + 결과 표시 영역 추가 |

---

## 리스크 및 완화 전략

| 리스크 | 영향도 | 완화 전략 |
|--------|--------|-----------|
| Sprint 0 미완료 시 레이아웃 기반 부재 | 높음 | Sprint 0 완료 확인 후 착수. 미완료 시 `app.py` 기본 셸부터 재구성 |
| `st.form`과 `st.columns` 중첩 레이아웃 깨짐 | 중간 | `st.columns` 바깥이 아닌 각 컬럼 내부에서 `st.form` 선언 |
| `st.code` 복사 아이콘이 내부망 환경에서 동작 안 할 경우 | 낮음 | `st.text_area(value=..., disabled=True)` 대체 사용 가능 |
| 고객사 목록 하드코딩 관리 부담 | 낮음 | Phase 3에서 `customers.json` 전환 예정. Sprint 1은 하드코딩으로 충분 |
