# Sprint 2: Claude 분석 + 질문 생성 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** "추가로 뭐가 더 필요할지 물어보기" 버튼 클릭 시 Claude API로 누락 필드 탐지, 질문 리스트, 추천 제목/Description, 리스크 플래그를 JSON으로 받아 Streamlit UI에 표시한다.

**Architecture:** `src/claude_analyzer.py`가 Anthropic Python SDK를 통해 Claude API를 호출하고 응답 JSON을 검증한다. `app.py`의 우측 컬럼에 분석 버튼과 결과 표시 UI를 추가한다. LLM 실패 시에도 Sprint 1의 기본 템플릿은 항상 정상 동작해야 하며, 에러는 친근한 메시지로 표시한다.

**Tech Stack:** Python 3.x, Streamlit, Anthropic Python SDK (`anthropic>=0.25.0`), `python-dotenv`, `pytest`, `unittest.mock`

---

## 스프린트 정보

- **기간:** 2026-04-03 ~ 2026-04-17 (2주)
- **MoSCoW:** Must Have (PRD 5.2)
- **마일스톤:** M2 - Claude 지능 분석
- **Karpathy:** Goal-Driven Execution — JSON 스키마 검증 성공이 완료 기준
- **의존성:** Sprint 1 완료 필요 (`app.py`에 `st.session_state["template_text"]` 등이 설정되어 있어야 함)

---

## 응답 JSON 스키마 (전체 스프린트 성공 기준)

```json
{
  "missing_fields": ["string"],
  "questions_to_ask": ["string"],
  "redmine_subject": "string",
  "redmine_description": "string",
  "confidence": 0.85,
  "risk_flags": ["PII_POSSIBLE"]
}
```

검증 순서: (1) JSON 파싱 성공 → (2) 필수 키 6개 존재 → (3) 타입 정합성 → (4) confidence 범위 0.0~1.0

---

## Task 1: 프로젝트 구조 준비 및 의존성 추가

**Files:**
- Modify: `requirements.txt`
- Create: `src/__init__.py`
- Create: `src/claude_analyzer.py` (빈 파일)
- Create: `tests/__init__.py` (없으면)
- Create: `tests/test_claude_analyzer.py` (빈 파일)

### Step 1: requirements.txt에 anthropic 추가

`requirements.txt` 파일이 존재하면 내용을 확인하고 없으면 새로 생성한다. 아래 항목이 포함되어 있는지 확인하고 없으면 추가한다.

```
streamlit
anthropic>=0.25.0
python-dotenv
requests
pytest
```

### Step 2: 디렉토리 및 초기 파일 생성

```bash
mkdir -p src tests
touch src/__init__.py tests/__init__.py
touch src/claude_analyzer.py tests/test_claude_analyzer.py
```

Expected: 명령어 오류 없이 완료

### Step 3: 의존성 설치

```bash
pip install -r requirements.txt
```

Expected: `Successfully installed anthropic-...` 또는 `Requirement already satisfied`

### Step 4: 임포트 동작 확인

```bash
python -c "import anthropic; print('anthropic OK')"
```

Expected: `anthropic OK`

### Step 5: Commit

```bash
git add requirements.txt src/__init__.py tests/__init__.py src/claude_analyzer.py tests/test_claude_analyzer.py
git commit -m "chore: add anthropic dependency and scaffold claude analyzer files"
```

---

## Task 2: JSON 검증 로직 실패 테스트 작성 (TDD)

**Files:**
- Modify: `tests/test_claude_analyzer.py`

### Step 1: 실패하는 테스트 작성

`tests/test_claude_analyzer.py`에 아래 내용을 작성한다.

```python
import pytest
from src.claude_analyzer import validate_response

def test_valid_response_passes():
    r = {"missing_fields": [], "questions_to_ask": [], "redmine_subject": "test", "redmine_description": "desc", "confidence": 0.8, "risk_flags": []}
    result = validate_response(r)
    assert result["confidence"] == 0.8

def test_missing_key_gets_default():
    r = {"missing_fields": [], "questions_to_ask": []}
    result = validate_response(r)
    assert result["redmine_subject"] == ""
    assert result["confidence"] == 0.0

def test_confidence_over_1_clamped():
    r = {"missing_fields": [], "questions_to_ask": [], "redmine_subject": "", "redmine_description": "", "confidence": 1.5, "risk_flags": []}
    result = validate_response(r)
    assert result["confidence"] == 1.0

def test_confidence_below_0_clamped():
    r = {"missing_fields": [], "questions_to_ask": [], "redmine_subject": "", "redmine_description": "", "confidence": -0.5, "risk_flags": []}
    result = validate_response(r)
    assert result["confidence"] == 0.0

def test_non_list_missing_fields_converted():
    r = {"missing_fields": "field1", "questions_to_ask": [], "redmine_subject": "", "redmine_description": "", "confidence": 0.5, "risk_flags": []}
    result = validate_response(r)
    assert isinstance(result["missing_fields"], list)

def test_invalid_json_string_returns_default():
    from src.claude_analyzer import parse_json_response
    result = parse_json_response("not json at all")
    assert result["confidence"] == 0.0

def test_json_in_markdown_fence_extracted():
    from src.claude_analyzer import parse_json_response
    text = '```json\n{"missing_fields": [], "questions_to_ask": [], "redmine_subject": "t", "redmine_description": "d", "confidence": 0.9, "risk_flags": []}\n```'
    result = parse_json_response(text)
    assert result["confidence"] == 0.9
```

### Step 2: 테스트 실행 - 실패 확인

```bash
pytest tests/test_claude_analyzer.py -v
```

Expected: `7 FAILED` (ImportError — `validate_response`, `parse_json_response` 미정의)

---

## Task 3: validate_response + parse_json_response 구현

**Files:**
- Modify: `src/claude_analyzer.py`

### Step 1: 구현 코드 작성

`src/claude_analyzer.py`에 아래 내용을 작성한다.

```python
import json
import re

DEFAULT_RESPONSE = {
    "missing_fields": [],
    "questions_to_ask": [],
    "redmine_subject": "",
    "redmine_description": "",
    "confidence": 0.0,
    "risk_flags": [],
}

def validate_response(data: dict) -> dict:
    result = DEFAULT_RESPONSE.copy()
    for key in DEFAULT_RESPONSE:
        if key in data:
            result[key] = data[key]
    if not isinstance(result["missing_fields"], list):
        result["missing_fields"] = [result["missing_fields"]]
    if not isinstance(result["questions_to_ask"], list):
        result["questions_to_ask"] = [result["questions_to_ask"]]
    if not isinstance(result["risk_flags"], list):
        result["risk_flags"] = [result["risk_flags"]]
    result["confidence"] = max(0.0, min(1.0, float(result["confidence"] or 0.0)))
    return result

def parse_json_response(text: str) -> dict:
    # 마크다운 코드펜스 제거
    fence_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1)
    try:
        return validate_response(json.loads(text))
    except (json.JSONDecodeError, ValueError):
        return DEFAULT_RESPONSE.copy()
```

### Step 2: 테스트 실행 - 통과 확인

```bash
pytest tests/test_claude_analyzer.py -v
```

Expected: `7 passed`

### Step 3: Commit

```bash
git add src/claude_analyzer.py tests/test_claude_analyzer.py
git commit -m "feat: implement JSON response validation and parse_json_response with TDD"
```

---

## Task 4: analyze_issue 실패 테스트 작성 (Mock API)

**Files:**
- Modify: `tests/test_claude_analyzer.py`

### Step 1: 실패하는 테스트 추가

`tests/test_claude_analyzer.py` 하단에 아래 테스트를 추가한다.

```python
from unittest.mock import patch, MagicMock
from src.claude_analyzer import analyze_issue

def test_analyze_issue_returns_parsed_json():
    mock_response_text = '{"missing_fields": ["steps"], "questions_to_ask": ["재현 절차를 알려주세요"], "redmine_subject": "[대웅제약] 주문 저장 오류", "redmine_description": "...", "confidence": 0.85, "risk_flags": []}'
    with patch("src.claude_analyzer.anthropic.Anthropic") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_message = MagicMock()
        mock_message.content[0].text = mock_response_text
        mock_client.messages.create.return_value = mock_message
        result, error = analyze_issue("템플릿 내용", {"tracker": "Defect", "customer": "대웅제약"}, "api_key")
    assert error is None
    assert result["confidence"] == 0.85

def test_analyze_issue_retries_on_bad_json():
    bad_json = "not json"
    good_json = '{"missing_fields": [], "questions_to_ask": [], "redmine_subject": "t", "redmine_description": "d", "confidence": 0.5, "risk_flags": []}'
    with patch("src.claude_analyzer.anthropic.Anthropic") as mock_class:
        mock_client = MagicMock()
        mock_class.return_value = mock_client
        mock1, mock2 = MagicMock(), MagicMock()
        mock1.content[0].text = bad_json
        mock2.content[0].text = good_json
        mock_client.messages.create.side_effect = [mock1, mock2]
        result, error = analyze_issue("템플릿", {}, "api_key")
    assert error is None
    assert result["confidence"] == 0.5

def test_analyze_issue_api_error_returns_error():
    import anthropic
    with patch("src.claude_analyzer.anthropic.Anthropic") as mock_class:
        mock_client = MagicMock()
        mock_class.return_value = mock_client
        mock_client.messages.create.side_effect = anthropic.APIConnectionError(request=MagicMock())
        result, error = analyze_issue("템플릿", {}, "api_key")
    assert result is None
    assert error is not None
```

### Step 2: 테스트 실행 - 실패 확인

```bash
pytest tests/test_claude_analyzer.py -v
```

Expected: `3 FAILED` (ImportError — `analyze_issue` 미정의)

---

## Task 5: analyze_issue 구현

**Files:**
- Modify: `src/claude_analyzer.py`

### Step 1: 구현 코드 추가

`src/claude_analyzer.py` 하단에 아래 내용을 이어 붙인다 (기존 `validate_response`, `parse_json_response` 아래).

```python
import anthropic
import os

SYSTEM_PROMPT = """당신은 소프트웨어 이슈 분석 전문가입니다.
이슈 내용을 분석하여 누락된 정보와 추가로 확인해야 할 사항을 JSON으로 반환하세요.
⚠️ PII 주의: 주민번호/전화번호/환자명 등 PII 원문을 요구하지 마세요. 마스킹된 키값이나 내부 ID로만 요청하세요.
반드시 아래 JSON 형식으로만 응답하세요:
{"missing_fields": [], "questions_to_ask": [], "redmine_subject": "", "redmine_description": "", "confidence": 0.0, "risk_flags": []}"""

def analyze_issue(template: str, meta: dict, api_key: str) -> tuple:
    """
    레드마인 이슈 템플릿을 Claude에 전달하여 분석 결과를 반환한다.

    Returns:
        (result_dict, None)  - 성공 시
        (None, error_str)    - 실패 시
    """
    try:
        client = anthropic.Anthropic(api_key=api_key)
        user_content = f"Tracker: {meta.get('tracker', '')}, 고객사: {meta.get('customer', '')}\n\n{template}"

        def _call():
            return client.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_content}]
            )

        response = _call()
        result = parse_json_response(response.content[0].text)

        # 파싱 실패 시 1회 재시도 (confidence==0.0 이고 subject 비어있으면 실패로 판단)
        if result["confidence"] == 0.0 and not result["redmine_subject"]:
            response = _call()
            result = parse_json_response(response.content[0].text)

        return result, None
    except anthropic.APIConnectionError as e:
        return None, f"연결 오류: {str(e)}"
    except anthropic.AuthenticationError:
        return None, "Claude API 키가 설정되지 않았어요. .env 파일을 확인해주세요."
    except Exception as e:
        return None, f"지금은 버그버디가 쉬는 중이에요. 나중에 다시 시도해 주세요. ({type(e).__name__})"
```

### Step 2: 테스트 실행 - 전체 통과 확인

```bash
pytest tests/test_claude_analyzer.py -v
```

Expected: `10 passed` (기존 7개 + 새 3개)

### Step 3: Commit

```bash
git add src/claude_analyzer.py tests/test_claude_analyzer.py
git commit -m "feat: implement analyze_issue with Claude API call, retry logic, and error handling"
```

---

## Task 6: "추가로 뭐가 더 필요할지 물어보기" 버튼 UI 구현

**Files:**
- Modify: `app.py`

**전제 조건:** Sprint 1에서 `app.py`에 다음이 구현되어 있어야 한다.
- `st.session_state["template_text"]`: 생성된 템플릿 문자열
- `st.session_state["tracker"]`, `["status"]`, `["start_date"]`, `["customer"]`: 입력 폼 값

### Step 1: 임포트 추가

`app.py` 상단 임포트 섹션에 아래를 추가한다.

```python
import os
from src.claude_analyzer import analyze_issue
```

### Step 2: 분석 버튼 및 결과 표시 코드 추가

템플릿 출력 영역 바로 아래(우측 컬럼)에 아래 코드 블록을 추가한다.

```python
# ──────────────────────────────────────────────
# Claude 분석 버튼 (템플릿이 생성된 후에만 활성화)
# ──────────────────────────────────────────────
template_ready = bool(st.session_state.get("template_text", ""))

if st.button(
    "🔍 추가로 뭐가 더 필요할지 물어보기",
    disabled=not template_ready,
    key="btn_analyze",
):
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    with st.spinner("버그버디가 분석하고 있어요..."):
        result, error = analyze_issue(
            template=st.session_state["template_text"],
            meta={
                "tracker": st.session_state.get("tracker", ""),
                "customer": st.session_state.get("customer", ""),
            },
            api_key=api_key,
        )
    st.session_state["analysis_result"] = result
    st.session_state["analysis_error"] = error

# ──────────────────────────────────────────────
# 분석 결과 표시
# ──────────────────────────────────────────────
if "analysis_error" in st.session_state and st.session_state["analysis_error"]:
    st.error(st.session_state["analysis_error"])

elif "analysis_result" in st.session_state and st.session_state["analysis_result"]:
    data = st.session_state["analysis_result"]
    st.divider()
    st.subheader("버그버디 분석 결과")

    # 1. 추천 제목 (편집 가능)
    st.text_input(
        "추천 제목",
        value=data["redmine_subject"],
        key="edited_subject",
    )

    # 2. 정제된 Description (편집 가능)
    st.text_area(
        "정제된 Description",
        value=data["redmine_description"],
        height=200,
        key="edited_description",
    )

    # 3. 누락 필드
    if data["missing_fields"]:
        st.warning("누락 가능성: " + ", ".join(data["missing_fields"]))

    # 4. 추가 질문 리스트 (복사 가능)
    if data["questions_to_ask"]:
        st.markdown("**추가로 확인이 필요한 사항:**")
        questions_text = "\n".join(
            f"{i+1}. {q}" for i, q in enumerate(data["questions_to_ask"])
        )
        st.code(questions_text, language=None)

    # 5. 신뢰도
    st.markdown(f"**신뢰도:** {data['confidence']:.0%}")
    st.progress(data["confidence"])

    # 6. 리스크 플래그
    for flag in data["risk_flags"]:
        st.error(f"⚠️ {flag}")

    # 7. JSON 디버그 뷰
    with st.expander("디버그: JSON 원본"):
        st.json(data)
```

### Step 3: 앱 실행 확인 (수동)

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속 후:
1. 이슈 정보 입력 전: "추가로 뭐가 더 필요할지 물어보기" 버튼이 비활성화(disabled) 상태인지 확인
2. "버그버디에게 정리 부탁하기" 클릭 → 템플릿 생성 확인
3. 버튼이 활성화되는지 확인
4. 버튼 클릭 → 스피너 → 분석 결과 표시 확인

Expected: 에러 없이 UI가 렌더링되고 버튼 활성/비활성이 올바르게 작동함

### Step 4: Commit

```bash
git add app.py
git commit -m "feat: add Claude analysis button and result display UI in app.py"
```

---

## Task 7: 에러 처리 시나리오 수동 검증

**Files:**
- Modify: `.env` (검증 목적, 커밋 대상 아님)
- Modify: `app.py` (필요 시 에러 메시지 문구 수정)

이 태스크는 자동화 테스트가 아닌 수동 시나리오 검증이다.

### Step 1: API 키 미설정 시나리오 검증

`.env`에서 `ANTHROPIC_API_KEY` 값을 비우거나 제거한 후 앱을 재시작한다.

```bash
streamlit run app.py
```

1. 이슈 입력 후 "버그버디에게 정리 부탁하기" 클릭 → 템플릿 생성
2. "🔍 추가로 뭐가 더 필요할지 물어보기" 클릭

Expected:
- `st.error`로 "Claude API 키가 설정되지 않았어요. .env 파일을 확인해주세요." 메시지 표시
- 기본 템플릿(7개 섹션)은 우측에 여전히 표시됨

### Step 2: 에러 메시지 문구 최종 점검

다음 3가지 에러 메시지가 UI와 `src/claude_analyzer.py` 코드에서 일치하는지 확인한다.

- API 키 미설정: `"Claude API 키가 설정되지 않았어요. .env 파일을 확인해주세요."`
- 연결 오류: `"연결 오류: ..."`
- 기타 예외: `"지금은 버그버디가 쉬는 중이에요. 나중에 다시 시도해 주세요."`

### Step 3: API 키 복원 후 정상 흐름 재확인

`.env`에 유효한 `ANTHROPIC_API_KEY` 복원 후 앱 재시작, 전체 흐름 확인:
- 분석 결과 6개 영역(추천 제목, Description, 누락 필드, 질문 리스트, 신뢰도, 리스크 플래그)이 모두 표시되는지 확인

### Step 4: Commit (문구 수정이 있었다면)

```bash
git add app.py src/claude_analyzer.py
git commit -m "fix: align error messages with UX copy spec"
```

---

## Task 8: Playwright MCP 통합 검증

**전제 조건:** `ANTHROPIC_API_KEY`가 유효한 상태, `streamlit run app.py` 실행 중

### 시나리오 A: Claude 분석 정상 흐름

```
1. browser_navigate → http://localhost:8501
2. browser_select_option → Tracker="Defect", 고객사="대웅제약"
3. browser_type → 에러 내용 필드에 "SFE 앱에서 주문 등록 시 저장 버튼 클릭하면 화면이 멈추는 현상" 입력
4. browser_click → "버그버디에게 정리 부탁하기"
5. browser_wait_for → "(1) 에러 내용" 텍스트 출현 대기
6. browser_click → "🔍 추가로 뭐가 더 필요할지 물어보기"
7. browser_wait_for → "버그버디가 분석하고 있어요" 로딩 표시 대기
8. browser_wait_for → "버그버디 분석 결과" 헤더 출현 대기 (최대 15초)
9. browser_snapshot → 추천 제목/Description/질문 리스트/신뢰도/리스크 플래그 확인
10. browser_click → "디버그: JSON 원본" expander 클릭
11. browser_snapshot → JSON 원본 표시 확인
12. browser_console_messages(level: "error") → 에러 없음 확인
```

### 시나리오 B: API 키 미설정 에러 처리

```
(.env에서 ANTHROPIC_API_KEY 제거 후 앱 재시작)
1. browser_navigate → http://localhost:8501
2. 이슈 입력 후 "버그버디에게 정리 부탁하기" 클릭
3. browser_click → "🔍 추가로 뭐가 더 필요할지 물어보기"
4. browser_wait_for → "Claude API 키가 설정되지 않았어요" 메시지 대기
5. browser_snapshot → 에러 메시지 확인 + 기본 템플릿 여전히 표시됨 확인
```

---

## Task 9: 전체 테스트 스위트 최종 실행 및 완료 확인

**Files:**
- Modify: `tests/test_claude_analyzer.py` (필요 시 누락 케이스 추가)

### Step 1: 전체 테스트 실행

```bash
pytest tests/test_claude_analyzer.py -v --tb=short
```

Expected 출력:

```
tests/test_claude_analyzer.py::test_valid_response_passes PASSED
tests/test_claude_analyzer.py::test_missing_key_gets_default PASSED
tests/test_claude_analyzer.py::test_confidence_over_1_clamped PASSED
tests/test_claude_analyzer.py::test_confidence_below_0_clamped PASSED
tests/test_claude_analyzer.py::test_non_list_missing_fields_converted PASSED
tests/test_claude_analyzer.py::test_invalid_json_string_returns_default PASSED
tests/test_claude_analyzer.py::test_json_in_markdown_fence_extracted PASSED
tests/test_claude_analyzer.py::test_analyze_issue_returns_parsed_json PASSED
tests/test_claude_analyzer.py::test_analyze_issue_retries_on_bad_json PASSED
tests/test_claude_analyzer.py::test_analyze_issue_api_error_returns_error PASSED

10 passed in X.XXs
```

### Step 2: 완료 기준 체크리스트

- [ ] "추가로 뭐가 더 필요할지 물어보기" 버튼 클릭 → Claude 호출 → JSON 결과 표시
- [ ] 버튼이 템플릿 미생성 시 비활성화(disabled)됨
- [ ] 추천 제목/Description이 편집 가능한 필드로 표시됨 (`st.text_input`, `st.text_area`)
- [ ] 질문 리스트가 `st.code`로 복사 가능한 형태로 표시됨
- [ ] 리스크 플래그가 `st.error("⚠️ ...")` 형태로 표시됨
- [ ] JSON 디버그 뷰가 `st.expander("디버그: JSON 원본")`으로 제공됨
- [ ] API 키 미설정 시 "Claude API 키가 설정되지 않았어요." 표시
- [ ] 호출 실패 시 "지금은 버그버디가 쉬는 중이에요." 표시
- [ ] LLM 실패 시에도 기본 템플릿(7개 섹션)이 정상 표시됨
- [ ] `pytest tests/test_claude_analyzer.py` 10개 전체 통과

### Step 3: 최종 Commit

```bash
git add .
git commit -m "feat: complete Sprint 2 - Claude analysis integration

- Implement claude_analyzer.py with JSON validation and retry logic
- Add 'Ask what else is needed' button and result display UI
- Support editing of recommended subject/description
- Display risk flags, confidence bar, and debug expander
- Full test coverage with Mock (10 tests pass)
- Friendly error messages for API key missing / network error"
```

---

## 리스크 및 대응 전략

| 리스크 | 영향도 | 완화 전략 |
|--------|--------|-----------|
| Claude 응답이 JSON이 아닌 자유 텍스트 | 높음 | 시스템 프롬프트에 JSON 출력 강제 + `parse_json_response`에서 마크다운 펜스 제거 + 1회 재시도 |
| `confidence`가 문자열로 올 수 있음 | 중간 | `float()` 변환 + 예외 시 기본값 0.0 사용 |
| `anthropic.AuthenticationError` 생성자 시그니처 SDK 버전 간 차이 | 낮음 | `requirements.txt`에 `anthropic>=0.25.0` 버전 고정 |
| Streamlit `session_state` 초기화 타이밍 | 중간 | `st.session_state.get("key", "")` 패턴으로 기본값 처리 |
| PII가 Claude로 전송될 위험 | 높음 | 시스템 프롬프트 PII 가이드 포함 + UI 입력란에 경고 문구(Sprint 1 구현) |

---

## 기술 고려사항

- **JSON 파싱:** Claude 응답에 마크다운 코드 블록(` ```json `)이 포함될 수 있으므로 `parse_json_response`에서 정규식으로 펜스 제거 처리.
- **streaming 미사용:** `client.messages.create` 기본 동기 호출 사용. Streamlit에서 streaming은 불필요.
- **`max_tokens=2048`:** 요청당 토큰 비용 관리를 위해 고정값 사용.
- **Streamlit 캐싱 미적용:** 분석 결과는 이슈마다 다르므로 `@st.cache_data` 적용하지 않음.
- **재시도 판단 기준:** `confidence == 0.0` AND `redmine_subject == ""` 동시에 성립할 때만 재시도. 의도적으로 낮은 confidence를 반환한 정상 응답은 재시도하지 않음.
