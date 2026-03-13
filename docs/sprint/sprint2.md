# Sprint 2: Claude 분석 + 질문 생성 구현 계획

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 생성된 레드마인 템플릿을 Claude에 전달하여 누락 필드 탐지, 추가 질문 리스트, 추천 제목/Description, 리스크 플래그를 JSON으로 받아 Streamlit UI에 표시한다.

**Architecture:** `src/claude_analyzer.py`가 Anthropic Python SDK를 통해 Claude API를 호출하고, 응답 JSON을 검증한 뒤 `app.py`의 Streamlit UI에 결과를 표시한다. LLM 실패 시에도 Sprint 1의 기본 템플릿은 항상 정상 동작해야 하며, 에러 상태는 친근한 메시지로 표시한다.

**Tech Stack:** Python 3.x, Streamlit, Anthropic Python SDK (`anthropic`), `python-dotenv`, `pytest`, `unittest.mock`

**스프린트 정보:**
- 기간: 2026-04-03 ~ 2026-04-17 (2주)
- MoSCoW: Must Have (PRD 5.2)
- 마일스톤: M2 - Claude 지능 분석
- Karpathy Guideline: Goal-Driven Execution (JSON 스키마 검증이 성공 기준)
- 의존성: Sprint 1 완료 필요 (템플릿 출력이 Claude 입력)

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
- Create: `tests/__init__.py`
- Create: `tests/test_claude_analyzer.py` (빈 파일)

**Step 1: requirements.txt에 anthropic 패키지 추가**

`requirements.txt`에 다음 내용이 포함되어 있는지 확인하고, 없으면 추가한다.

```
streamlit
anthropic
python-dotenv
requests
pytest
```

**Step 2: 디렉토리 및 초기 파일 생성**

```bash
mkdir -p src tests
touch src/__init__.py tests/__init__.py
touch src/claude_analyzer.py tests/test_claude_analyzer.py
```

**Step 3: 의존성 설치 확인**

```bash
pip install -r requirements.txt
```

Expected: `Successfully installed anthropic-...` 또는 `Requirement already satisfied`

**Step 4: 모듈 임포트 동작 확인**

```bash
python -c "import anthropic; print('anthropic OK')"
```

Expected: `anthropic OK`

**Step 5: Commit**

```bash
git add requirements.txt src/__init__.py tests/__init__.py src/claude_analyzer.py tests/test_claude_analyzer.py
git commit -m "chore: add anthropic dependency and scaffold claude analyzer files"
```

---

## Task 2: JSON 검증 로직 구현 (TDD)

**Files:**
- Modify: `src/claude_analyzer.py`
- Modify: `tests/test_claude_analyzer.py`

이 태스크는 Claude API 호출 없이 순수 Python 로직만 다루므로 Mock 없이 테스트 가능하다.

### Step 1: 실패하는 테스트 작성

`tests/test_claude_analyzer.py`에 아래 내용을 작성한다.

```python
import pytest
from src.claude_analyzer import validate_analysis_response, DEFAULT_RESPONSE


class TestValidateAnalysisResponse:
    """JSON 응답 검증 로직 테스트"""

    def test_valid_response_passes(self):
        """정상적인 JSON 응답은 그대로 반환된다"""
        valid = {
            "missing_fields": ["재현 절차"],
            "questions_to_ask": ["몇 번 재현되었나요?"],
            "redmine_subject": "[대웅제약] SFE 주문 등록 저장 버튼 클릭 시 화면 멈춤",
            "redmine_description": "## 에러 내용\n저장 버튼 클릭 후 화면 멈춤",
            "confidence": 0.85,
            "risk_flags": [],
        }
        result = validate_analysis_response(valid)
        assert result["redmine_subject"] == valid["redmine_subject"]
        assert result["confidence"] == 0.85

    def test_missing_key_falls_back_to_default(self):
        """필수 키가 없으면 기본값 fallback을 반환한다"""
        incomplete = {
            "missing_fields": [],
            "questions_to_ask": [],
            # redmine_subject 누락
            "redmine_description": "설명",
            "confidence": 0.5,
            "risk_flags": [],
        }
        result = validate_analysis_response(incomplete)
        assert result["redmine_subject"] == DEFAULT_RESPONSE["redmine_subject"]

    def test_confidence_above_1_is_clamped(self):
        """confidence가 1.0을 초과하면 1.0으로 클램핑된다"""
        data = {
            "missing_fields": [],
            "questions_to_ask": [],
            "redmine_subject": "제목",
            "redmine_description": "설명",
            "confidence": 1.5,
            "risk_flags": [],
        }
        result = validate_analysis_response(data)
        assert result["confidence"] == 1.0

    def test_confidence_below_0_is_clamped(self):
        """confidence가 0.0 미만이면 0.0으로 클램핑된다"""
        data = {
            "missing_fields": [],
            "questions_to_ask": [],
            "redmine_subject": "제목",
            "redmine_description": "설명",
            "confidence": -0.3,
            "risk_flags": [],
        }
        result = validate_analysis_response(data)
        assert result["confidence"] == 0.0

    def test_confidence_not_float_falls_back(self):
        """confidence가 숫자가 아니면 기본값 fallback을 반환한다"""
        data = {
            "missing_fields": [],
            "questions_to_ask": [],
            "redmine_subject": "제목",
            "redmine_description": "설명",
            "confidence": "높음",  # 문자열은 타입 오류
            "risk_flags": [],
        }
        result = validate_analysis_response(data)
        assert result["confidence"] == DEFAULT_RESPONSE["confidence"]

    def test_missing_fields_not_list_falls_back(self):
        """missing_fields가 리스트가 아니면 기본값 fallback을 반환한다"""
        data = {
            "missing_fields": "재현 절차",  # 리스트가 아님
            "questions_to_ask": [],
            "redmine_subject": "제목",
            "redmine_description": "설명",
            "confidence": 0.5,
            "risk_flags": [],
        }
        result = validate_analysis_response(data)
        assert isinstance(result["missing_fields"], list)

    def test_empty_dict_returns_default(self):
        """빈 딕셔너리는 전체 기본값을 반환한다"""
        result = validate_analysis_response({})
        assert result == DEFAULT_RESPONSE
```

**Step 2: 테스트 실행 - 실패 확인**

```bash
pytest tests/test_claude_analyzer.py -v
```

Expected: `ImportError` 또는 `ModuleNotFoundError` (아직 구현 없음)

**Step 3: 검증 로직 구현**

`src/claude_analyzer.py`에 아래 내용을 작성한다.

```python
"""
Claude 분석 서비스

Anthropic Python SDK를 사용하여 레드마인 이슈 템플릿을 분석하고
누락 필드, 추가 질문, 추천 제목/Description, 리스크 플래그를 반환한다.
"""
from __future__ import annotations

# ──────────────────────────────────────────────
# 필수 키 목록 (JSON 스키마 기준)
# ──────────────────────────────────────────────
REQUIRED_KEYS = [
    "missing_fields",
    "questions_to_ask",
    "redmine_subject",
    "redmine_description",
    "confidence",
    "risk_flags",
]

# 검증 실패 시 반환할 기본값
DEFAULT_RESPONSE: dict = {
    "missing_fields": [],
    "questions_to_ask": [],
    "redmine_subject": "",
    "redmine_description": "",
    "confidence": 0.0,
    "risk_flags": [],
}


def validate_analysis_response(data: dict) -> dict:
    """
    Claude 응답 JSON을 검증하고 정제된 딕셔너리를 반환한다.

    검증 순서:
    1. 필수 키 6개 모두 존재하는지 확인
    2. missing_fields, questions_to_ask, risk_flags 가 list인지 확인
    3. redmine_subject, redmine_description 이 str인지 확인
    4. confidence 가 float/int이고 0.0~1.0 범위인지 확인 (초과 시 클램핑)

    검증 실패 시 DEFAULT_RESPONSE 반환.
    """
    # 필수 키 존재 확인
    for key in REQUIRED_KEYS:
        if key not in data:
            return dict(DEFAULT_RESPONSE)

    # 리스트 타입 검증
    for list_key in ("missing_fields", "questions_to_ask", "risk_flags"):
        if not isinstance(data[list_key], list):
            return dict(DEFAULT_RESPONSE)

    # 문자열 타입 검증
    for str_key in ("redmine_subject", "redmine_description"):
        if not isinstance(data[str_key], str):
            return dict(DEFAULT_RESPONSE)

    # confidence 타입 및 범위 검증
    confidence = data["confidence"]
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
        return dict(DEFAULT_RESPONSE)

    # 범위 클램핑 (0.0 ~ 1.0)
    clamped_confidence = max(0.0, min(1.0, float(confidence)))

    return {
        "missing_fields": data["missing_fields"],
        "questions_to_ask": data["questions_to_ask"],
        "redmine_subject": data["redmine_subject"],
        "redmine_description": data["redmine_description"],
        "confidence": clamped_confidence,
        "risk_flags": data["risk_flags"],
    }
```

**Step 4: 테스트 실행 - 통과 확인**

```bash
pytest tests/test_claude_analyzer.py::TestValidateAnalysisResponse -v
```

Expected: 7개 테스트 모두 PASS

**Step 5: Commit**

```bash
git add src/claude_analyzer.py tests/test_claude_analyzer.py
git commit -m "feat: implement JSON response validation logic with TDD"
```

---

## Task 3: Claude API 호출 서비스 구현 (Mock TDD)

**Files:**
- Modify: `src/claude_analyzer.py`
- Modify: `tests/test_claude_analyzer.py`

### Step 1: 실패하는 테스트 작성

`tests/test_claude_analyzer.py` 하단에 아래 테스트 클래스를 추가한다.

```python
import json
from unittest.mock import MagicMock, patch


class TestAnalyzeIssue:
    """Claude API 호출 및 응답 파싱 테스트 (Mock 사용)"""

    VALID_JSON_RESPONSE = json.dumps({
        "missing_fields": ["재현 절차", "발생 환경"],
        "questions_to_ask": ["몇 번 재현되었나요?", "어떤 브라우저를 사용하셨나요?"],
        "redmine_subject": "[대웅제약] SFE 주문 등록 저장 버튼 클릭 시 화면 멈춤",
        "redmine_description": "## 에러 내용\n저장 버튼 클릭 후 화면 멈춤 현상 발생",
        "confidence": 0.82,
        "risk_flags": [],
    })

    def _make_mock_client(self, response_text: str):
        """Anthropic 클라이언트 Mock 생성 헬퍼"""
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=response_text)]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message
        return mock_client

    def test_valid_response_returns_parsed_result(self):
        """정상 JSON 응답은 검증된 딕셔너리를 반환한다"""
        from src.claude_analyzer import analyze_issue

        mock_client = self._make_mock_client(self.VALID_JSON_RESPONSE)

        with patch("src.claude_analyzer._get_client", return_value=mock_client):
            result = analyze_issue(
                template_text="템플릿 내용",
                tracker="Defect",
                status="New",
                start_date="2026-04-03",
                customer="대웅제약",
            )

        assert result["success"] is True
        assert result["data"]["redmine_subject"] == "[대웅제약] SFE 주문 등록 저장 버튼 클릭 시 화면 멈춤"
        assert result["data"]["confidence"] == 0.82
        assert len(result["data"]["questions_to_ask"]) == 2

    def test_invalid_json_retries_once_and_fails(self):
        """JSON 파싱 실패 시 1회 재시도 후 에러를 반환한다"""
        from src.claude_analyzer import analyze_issue

        mock_client = self._make_mock_client("이건 JSON이 아닙니다. 자유 텍스트 응답입니다.")

        with patch("src.claude_analyzer._get_client", return_value=mock_client):
            result = analyze_issue(
                template_text="템플릿 내용",
                tracker="Defect",
                status="New",
                start_date="2026-04-03",
                customer="대웅제약",
            )

        # 2회 호출 (최초 1회 + 재시도 1회)
        assert mock_client.messages.create.call_count == 2
        assert result["success"] is False
        assert "error" in result

    def test_invalid_json_then_valid_json_on_retry(self):
        """첫 번째 응답이 잘못된 JSON이고 재시도에서 올바른 JSON을 받으면 성공한다"""
        from src.claude_analyzer import analyze_issue

        mock_message_bad = MagicMock()
        mock_message_bad.content = [MagicMock(text="잘못된 응답")]

        mock_message_good = MagicMock()
        mock_message_good.content = [MagicMock(text=self.VALID_JSON_RESPONSE)]

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [mock_message_bad, mock_message_good]

        with patch("src.claude_analyzer._get_client", return_value=mock_client):
            result = analyze_issue(
                template_text="템플릿 내용",
                tracker="Defect",
                status="New",
                start_date="2026-04-03",
                customer="대웅제약",
            )

        assert mock_client.messages.create.call_count == 2
        assert result["success"] is True

    def test_api_key_not_set_returns_error(self):
        """API 키 미설정 시 친근한 에러 메시지를 반환한다"""
        from src.claude_analyzer import analyze_issue
        import anthropic

        with patch("src.claude_analyzer._get_client",
                   side_effect=anthropic.AuthenticationError(
                       message="invalid api key",
                       response=MagicMock(status_code=401),
                       body={}
                   )):
            result = analyze_issue(
                template_text="템플릿 내용",
                tracker="Defect",
                status="New",
                start_date="2026-04-03",
                customer="대웅제약",
            )

        assert result["success"] is False
        assert "API 키" in result["error"]

    def test_network_error_returns_friendly_message(self):
        """네트워크 에러 시 친근한 에러 메시지를 반환한다"""
        from src.claude_analyzer import analyze_issue

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("Connection refused")

        with patch("src.claude_analyzer._get_client", return_value=mock_client):
            result = analyze_issue(
                template_text="템플릿 내용",
                tracker="Defect",
                status="New",
                start_date="2026-04-03",
                customer="대웅제약",
            )

        assert result["success"] is False
        assert "쉬는 중" in result["error"]

    def test_missing_required_key_in_response_falls_back(self):
        """응답 JSON에 필수 키가 없으면 DEFAULT_RESPONSE로 fallback한다"""
        from src.claude_analyzer import analyze_issue

        incomplete_json = json.dumps({
            "missing_fields": [],
            "questions_to_ask": [],
            # redmine_subject 누락
            "redmine_description": "설명",
            "confidence": 0.5,
            "risk_flags": [],
        })
        mock_client = self._make_mock_client(incomplete_json)

        with patch("src.claude_analyzer._get_client", return_value=mock_client):
            result = analyze_issue(
                template_text="템플릿 내용",
                tracker="Defect",
                status="New",
                start_date="2026-04-03",
                customer="대웅제약",
            )

        # 구조상 success는 True이나 data는 DEFAULT_RESPONSE
        assert result["success"] is True
        assert result["data"]["redmine_subject"] == ""
        assert result["data"]["confidence"] == 0.0
```

**Step 2: 테스트 실행 - 실패 확인**

```bash
pytest tests/test_claude_analyzer.py::TestAnalyzeIssue -v
```

Expected: `ImportError` - `analyze_issue`, `_get_client` 미정의

**Step 3: Claude API 호출 로직 구현**

`src/claude_analyzer.py`에 아래 내용을 추가한다 (기존 `validate_analysis_response` 아래에 이어 붙인다).

```python
import json
import os
import anthropic

# ──────────────────────────────────────────────
# 시스템 프롬프트
# ──────────────────────────────────────────────
_SYSTEM_PROMPT = """\
당신은 소프트웨어 이슈 분석 전문가입니다.
사용자가 제공하는 레드마인 이슈 초안을 분석하여 아래 JSON 형식으로만 응답하십시오.
다른 텍스트, 마크다운 코드 블록, 설명 없이 JSON만 출력하십시오.

출력 형식:
{
  "missing_fields": ["누락된 필드명 리스트"],
  "questions_to_ask": ["담당자에게 추가로 물어볼 질문 리스트"],
  "redmine_subject": "레드마인 제목 추천 (고객사명 포함, 간결하게)",
  "redmine_description": "정제된 레드마인 Description (마크다운 형식)",
  "confidence": 0.0에서 1.0 사이의 숫자,
  "risk_flags": ["PII_POSSIBLE 등 리스크 플래그 리스트"]
}

PII/PHI 가이드:
- 주민번호, 전화번호, 환자명 등 PII 원문을 요구하지 마십시오.
- 마스킹된 키값이나 내부 환자 ID 형태로 요청하십시오.
- PII가 포함되어 있다고 의심되면 risk_flags에 "PII_POSSIBLE"을 추가하십시오.
"""


def _get_client() -> anthropic.Anthropic:
    """Anthropic 클라이언트를 생성한다. API 키는 환경변수에서 읽는다."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise anthropic.AuthenticationError(
            message="ANTHROPIC_API_KEY가 설정되지 않았습니다.",
            response=None,
            body={},
        )
    return anthropic.Anthropic(api_key=api_key)


def _build_user_prompt(
    template_text: str,
    tracker: str,
    status: str,
    start_date: str,
    customer: str,
) -> str:
    """사용자 프롬프트를 조합한다."""
    return f"""\
[이슈 메타데이터]
- Tracker: {tracker}
- Status: {status}
- Start date: {start_date}
- 고객사: {customer}

[레드마인 이슈 초안]
{template_text}

위 이슈를 분석하여 JSON으로만 응답하십시오.
"""


def _call_claude(client: anthropic.Anthropic, user_prompt: str) -> str:
    """Claude API를 호출하고 텍스트 응답을 반환한다."""
    message = client.messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens=2048,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text


def analyze_issue(
    template_text: str,
    tracker: str,
    status: str,
    start_date: str,
    customer: str,
) -> dict:
    """
    레드마인 이슈 템플릿을 Claude에 전달하여 분석 결과를 반환한다.

    Returns:
        {
            "success": bool,
            "data": dict,   # validate_analysis_response 결과 (success=True 시)
            "error": str,   # 친근한 에러 메시지 (success=False 시)
        }
    """
    try:
        client = _get_client()
    except anthropic.AuthenticationError:
        return {
            "success": False,
            "error": "Claude API 키가 설정되지 않았어요. .env 파일을 확인해주세요.",
        }

    user_prompt = _build_user_prompt(template_text, tracker, status, start_date, customer)

    # 최대 1회 재시도
    for attempt in range(2):
        try:
            raw_text = _call_claude(client, user_prompt)
            parsed = json.loads(raw_text)
            validated = validate_analysis_response(parsed)
            return {"success": True, "data": validated}
        except json.JSONDecodeError:
            if attempt == 0:
                # 재시도 1회 허용
                continue
            return {
                "success": False,
                "error": "버그버디가 응답을 이해하지 못했어요. 다시 시도해 주세요.",
            }
        except anthropic.APITimeoutError:
            return {
                "success": False,
                "error": "버그버디가 너무 오래 고민하고 있어요. 다시 시도해 주세요.",
            }
        except Exception:
            return {
                "success": False,
                "error": "지금은 버그버디가 쉬는 중이에요. 나중에 다시 시도해 주세요.",
            }

    # 도달하지 않지만 명시적 반환
    return {
        "success": False,
        "error": "버그버디가 응답을 이해하지 못했어요. 다시 시도해 주세요.",
    }
```

**Step 4: 테스트 실행 - 통과 확인**

```bash
pytest tests/test_claude_analyzer.py -v
```

Expected: 전체 테스트 PASS (TestValidateAnalysisResponse 7개 + TestAnalyzeIssue 6개 = 13개)

**Step 5: Commit**

```bash
git add src/claude_analyzer.py tests/test_claude_analyzer.py
git commit -m "feat: implement Claude API caller with retry logic and error handling"
```

---

## Task 4: "추가로 뭐가 더 필요할지 물어보기" 버튼 및 분석 결과 UI 구현

**Files:**
- Modify: `app.py`

**전제 조건:** Sprint 1에서 `app.py`에 이미 다음이 구현되어 있어야 한다.
- `st.session_state["template_text"]`: 생성된 템플릿 문자열
- `st.session_state["tracker"]`, `["status"]`, `["start_date"]`, `["customer"]`: 입력 폼 값

### Step 1: app.py에서 claude_analyzer 임포트 추가

`app.py` 상단 임포트 섹션에 아래를 추가한다.

```python
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
    "추가로 뭐가 더 필요할지 물어보기",
    disabled=not template_ready,
    key="btn_analyze",
):
    with st.spinner("버그버디가 분석하고 있어요..."):
        result = analyze_issue(
            template_text=st.session_state["template_text"],
            tracker=st.session_state.get("tracker", ""),
            status=st.session_state.get("status", ""),
            start_date=str(st.session_state.get("start_date", "")),
            customer=st.session_state.get("customer", ""),
        )
    st.session_state["analysis_result"] = result

# ──────────────────────────────────────────────
# 분석 결과 표시
# ──────────────────────────────────────────────
if "analysis_result" in st.session_state:
    analysis = st.session_state["analysis_result"]

    if not analysis["success"]:
        # 에러 상태: 친근한 메시지 표시, 기본 템플릿은 계속 유지
        st.error(analysis["error"])
    else:
        data = analysis["data"]
        st.divider()
        st.subheader("버그버디 분석 결과")

        # 1. 추천 제목 (편집 가능)
        st.text_input(
            "추천 제목",
            value=data["redmine_subject"],
            key="edited_subject",
        )

        # 2. 정제된 Description (편집 가능 + 복사)
        st.text_area(
            "정제된 Description",
            value=data["redmine_description"],
            height=200,
            key="edited_description",
        )
        # st.code로 복사 가능한 뷰 제공
        with st.expander("복사용 Description"):
            st.code(data["redmine_description"], language="markdown")

        # 3. 누락 필드
        if data["missing_fields"]:
            st.warning("누락된 필드: " + ", ".join(data["missing_fields"]))

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
        if data["risk_flags"]:
            flag_badges = " ".join(
                f"`{flag}`" for flag in data["risk_flags"]
            )
            st.markdown(f"**리스크 플래그:** {flag_badges}")

        # 7. JSON 디버그 뷰
        with st.expander("디버그: JSON 원본"):
            st.json(data)
```

### Step 3: 앱 실행 확인 (수동)

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속 후:
1. 이슈 정보 입력
2. "버그버디에게 정리 부탁하기" 클릭 → 템플릿 생성 확인
3. "추가로 뭐가 더 필요할지 물어보기" 버튼이 활성화되는지 확인
4. 버튼이 템플릿 없을 때 비활성화되는지 확인

### Step 4: Commit

```bash
git add app.py
git commit -m "feat: add Claude analysis button and result display UI"
```

---

## Task 5: 에러 처리 시나리오 수동 검증

**Files:**
- Modify: `app.py` (필요 시 에러 메시지 문구 수정)
- Modify: `.env` (검증 목적, 커밋 대상 아님)

이 태스크는 자동화 테스트가 아닌 수동 시나리오 검증이다.

### Step 1: API 키 미설정 시나리오 검증

`.env`에서 `ANTHROPIC_API_KEY` 값을 비우거나 제거한다.

```bash
streamlit run app.py
```

1. 브라우저에서 `http://localhost:8501` 접속
2. 이슈 정보 입력 후 "버그버디에게 정리 부탁하기" 클릭
3. "추가로 뭐가 더 필요할지 물어보기" 클릭

Expected:
- `st.error`로 "Claude API 키가 설정되지 않았어요. .env 파일을 확인해주세요." 메시지 표시
- 기본 템플릿(7개 섹션)은 여전히 우측에 표시됨

### Step 2: API 키 복원 후 정상 흐름 재확인

`.env`에 유효한 `ANTHROPIC_API_KEY` 복원 후 앱 재시작, 전체 흐름 재확인.

### Step 3: 에러 메시지 문구 최종 점검

다음 3가지 에러 메시지가 UI에 정확히 표시되는지 코드와 대조 확인:
- API 키 미설정: "Claude API 키가 설정되지 않았어요. .env 파일을 확인해주세요."
- 네트워크 에러: "지금은 버그버디가 쉬는 중이에요. 나중에 다시 시도해 주세요."
- 타임아웃: "버그버디가 너무 오래 고민하고 있어요. 다시 시도해 주세요."

### Step 4: Commit (문구 수정이 있었다면)

```bash
git add app.py src/claude_analyzer.py
git commit -m "fix: align error messages with UX copy spec"
```

---

## Task 6: Playwright MCP 통합 검증

**전제 조건:** `ANTHROPIC_API_KEY`가 유효한 상태, `streamlit run app.py` 실행 중

이 태스크는 Playwright MCP를 통한 브라우저 자동화 검증이다. 수동으로 Playwright MCP 도구를 사용하거나, 향후 CI 파이프라인에 통합할 수 있다.

### 시나리오 A: Claude 분석 정상 흐름

```
1. browser_navigate → http://localhost:8501
2. browser_select_option → Tracker="Defect", 고객사="대웅제약"
3. browser_type → 에러 내용 필드에 "SFE 앱에서 주문 등록 시 저장 버튼 클릭하면 화면이 멈추는 현상" 입력
4. browser_click → "버그버디에게 정리 부탁하기"
5. browser_wait_for → "(1) 에러 내용" 텍스트 출현 대기
6. browser_click → "추가로 뭐가 더 필요할지 물어보기"
7. browser_wait_for → "버그버디가 분석하고 있어요" 로딩 표시 대기
8. browser_wait_for → "추천 제목" 텍스트 출현 대기 (최대 15초)
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
3. browser_click → "추가로 뭐가 더 필요할지 물어보기"
4. browser_wait_for → "Claude API 키가 설정되지 않았어요" 메시지 대기
5. browser_snapshot → 에러 메시지 확인 + 기본 템플릿 여전히 표시됨 확인
```

---

## Task 7: 전체 테스트 스위트 최종 실행 및 완료 확인

**Files:**
- Modify: `tests/test_claude_analyzer.py` (필요 시 누락 케이스 추가)

### Step 1: 전체 테스트 실행

```bash
pytest tests/test_claude_analyzer.py -v --tb=short
```

Expected 출력:
```
tests/test_claude_analyzer.py::TestValidateAnalysisResponse::test_valid_response_passes PASSED
tests/test_claude_analyzer.py::TestValidateAnalysisResponse::test_missing_key_falls_back_to_default PASSED
tests/test_claude_analyzer.py::TestValidateAnalysisResponse::test_confidence_above_1_is_clamped PASSED
tests/test_claude_analyzer.py::TestValidateAnalysisResponse::test_confidence_below_0_is_clamped PASSED
tests/test_claude_analyzer.py::TestValidateAnalysisResponse::test_confidence_not_float_falls_back PASSED
tests/test_claude_analyzer.py::TestValidateAnalysisResponse::test_missing_fields_not_list_falls_back PASSED
tests/test_claude_analyzer.py::TestValidateAnalysisResponse::test_empty_dict_returns_default PASSED
tests/test_claude_analyzer.py::TestAnalyzeIssue::test_valid_response_returns_parsed_result PASSED
tests/test_claude_analyzer.py::TestAnalyzeIssue::test_invalid_json_retries_once_and_fails PASSED
tests/test_claude_analyzer.py::TestAnalyzeIssue::test_invalid_json_then_valid_json_on_retry PASSED
tests/test_claude_analyzer.py::TestAnalyzeIssue::test_api_key_not_set_returns_error PASSED
tests/test_claude_analyzer.py::TestAnalyzeIssue::test_network_error_returns_friendly_message PASSED
tests/test_claude_analyzer.py::TestAnalyzeIssue::test_missing_required_key_in_response_falls_back PASSED

13 passed in X.XXs
```

### Step 2: 완료 기준 체크리스트 최종 확인

- [ ] "추가로 뭐가 더 필요할지 물어보기" 클릭 → Claude 호출 → JSON 결과 표시
- [ ] 추천 제목/Description이 편집 가능한 필드로 표시됨 (`st.text_input`, `st.text_area`)
- [ ] 질문 리스트가 `st.code`로 복사 가능한 형태로 표시됨
- [ ] 리스크 플래그(`PII_POSSIBLE` 등)가 배지(`\`...\``) 형태로 시각 구분됨
- [ ] JSON 디버그 뷰가 `st.expander("디버그: JSON 원본")`으로 제공됨
- [ ] API 키 미설정 시 "Claude API 키가 설정되지 않았어요." 표시
- [ ] 호출 실패 시 "지금은 버그버디가 쉬는 중이에요." 표시
- [ ] LLM 실패 시에도 기본 템플릿(7개 섹션)이 정상 표시됨
- [ ] `pytest tests/test_claude_analyzer.py` 13개 전체 통과

### Step 3: 최종 Commit

```bash
git add .
git commit -m "feat: complete Sprint 2 - Claude analysis integration

- Implement claude_analyzer.py with JSON validation and retry logic
- Add 'Ask what else is needed' button and result display UI
- Support editing of recommended subject/description
- Display risk flags, confidence bar, and debug expander
- Full test coverage with Mock (13 tests pass)
- Friendly error messages for API key missing / network error / timeout"
```

---

## 리스크 및 대응 전략

| 리스크 | 영향도 | 완화 전략 |
|--------|--------|-----------|
| Claude 응답이 JSON이 아닌 자유 텍스트 | 높음 | 시스템 프롬프트에 JSON 출력 강제 + `json.loads` 실패 시 1회 재시도 |
| confidence 타입이 문자열로 올 수 있음 | 중간 | `isinstance(confidence, (int, float))` 검증 + fallback |
| `anthropic.AuthenticationError` 생성자 시그니처 변경 | 낮음 | 테스트에서 `side_effect` 사용, 실제 SDK 버전 고정 (`requirements.txt`에 버전 명시 권장) |
| Streamlit 상태(`session_state`) 초기화 타이밍 | 중간 | `st.session_state.get("key", "")` 패턴으로 기본값 처리 |
| PII가 Claude로 전송될 위험 | 높음 | UI 경고문(Sprint 1 구현) + 시스템 프롬프트 PII 가이드 포함 |

---

## 기술 고려사항

- **JSON 파싱:** Claude 응답에 마크다운 코드 블록(` ```json `)이 포함될 수 있으므로, 필요 시 `re.search(r'\{.*\}', text, re.DOTALL)`로 JSON 부분만 추출하는 로직 추가를 검토한다.
- **streaming 불사용:** `client.messages.create`의 기본 동기 호출 사용. Streamlit v1에서 streaming은 불필요하다.
- **`max_tokens=2048`:** 요청당 토큰 비용 관리를 위해 고정값 사용.
- **Streamlit 캐싱 미적용:** 분석 결과는 이슈마다 다르므로 `@st.cache_data` 적용하지 않는다.
- **`anthropic` SDK 버전:** `requirements.txt`에 최소 버전 명시 권장 (예: `anthropic>=0.25.0`).
