# Sprint 4: Redmine Integration + v1 Release Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redmine REST API에서 Tracker/Status 목록을 읽어와 드롭다운을 동적 구성하고, v1 전체 통합 점검 및 README 작성으로 릴리스한다.

**Architecture:** `src/redmine_client.py`가 환경변수에서 자격증명을 읽어 Redmine REST API를 read-only로 호출한다. API 실패/미설정 시 하드코딩 fallback 상수를 반환한다. `src/redmine_config.py`는 app.py가 사용하는 단일 진입점으로, fallback 여부 플래그와 UX 메시지를 포함한 dict를 반환한다. Karpathy Surgical Changes 원칙에 따라 `app.py`의 드롭다운 교체 부분(2곳)만 수정하고 나머지 코드는 한 줄도 변경하지 않는다.

**Tech Stack:** Python 3.9+, Streamlit, `requests`, `python-dotenv`, `pytest`, `unittest.mock`

---

## Task 1: Redmine 클라이언트 실패 테스트 작성

**Files:**
- Create: `tests/test_redmine_client.py`

### Step 1: 실패하는 테스트 작성

`tests/test_redmine_client.py`를 생성하고 아래 내용을 작성한다.

```python
import pytest
from unittest.mock import patch, MagicMock
from src.redmine_client import get_trackers, get_issue_statuses

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
```

### Step 2: 테스트 실행 - 실패 확인

Run: `pytest tests/test_redmine_client.py -v`

Expected:
```
FAILED tests/test_redmine_client.py::test_get_trackers_success
FAILED tests/test_redmine_client.py::test_get_trackers_auth_failure
FAILED tests/test_redmine_client.py::test_get_trackers_connection_error
FAILED tests/test_redmine_client.py::test_get_trackers_timeout
FAILED tests/test_redmine_client.py::test_get_issue_statuses_success
FAILED tests/test_redmine_client.py::test_get_trackers_missing_env
6 failed
```

실패 원인: `ImportError` — `src.redmine_client`에 `get_trackers`, `get_issue_statuses`가 정의되지 않음

---

## Task 2: Redmine 클라이언트 구현

**Files:**
- Modify: `src/redmine_client.py`

### Step 1: redmine_client.py 구현

`src/redmine_client.py`에 아래 내용을 작성한다.

```python
import requests

TRACKER_FALLBACK = ["Common", "Feature", "Defect", "Request", "Patch", "Issue", "Review"]
STATUS_FALLBACK = ["New", "Confirm", "Assigned", "In progress", "Resolved", "Closed", "Need Feedback", "Rejected"]

def get_trackers(base_url: str, api_key: str) -> tuple[list | None, str | None]:
    if not base_url or not api_key:
        return None, "Redmine URL 또는 API 키가 설정되지 않았어요."
    try:
        resp = requests.get(
            f"{base_url.rstrip('/')}/trackers.json",
            headers={"X-Redmine-API-Key": api_key},
            timeout=5
        )
        if resp.status_code == 401:
            return None, "Redmine 인증에 실패했어요. API 키를 확인해주세요."
        resp.raise_for_status()
        return resp.json().get("trackers", []), None
    except requests.Timeout:
        return None, "Redmine 연결이 타임아웃됐어요."
    except requests.ConnectionError:
        return None, "Redmine에 연결할 수 없어요."
    except Exception as e:
        return None, f"Redmine 오류: {e}"

def get_issue_statuses(base_url: str, api_key: str) -> tuple[list | None, str | None]:
    if not base_url or not api_key:
        return None, "Redmine URL 또는 API 키가 설정되지 않았어요."
    try:
        resp = requests.get(
            f"{base_url.rstrip('/')}/issue_statuses.json",
            headers={"X-Redmine-API-Key": api_key},
            timeout=5
        )
        if resp.status_code == 401:
            return None, "Redmine 인증에 실패했어요."
        resp.raise_for_status()
        return resp.json().get("issue_statuses", []), None
    except requests.Timeout:
        return None, "Redmine 연결이 타임아웃됐어요."
    except requests.ConnectionError:
        return None, "Redmine에 연결할 수 없어요."
    except Exception as e:
        return None, f"Redmine 오류: {e}"

def create_issue(*args, **kwargs):
    raise NotImplementedError("v2에서 구현 예정")
```

### Step 2: 테스트 실행 - 통과 확인

Run: `pytest tests/test_redmine_client.py -v`

Expected:
```
PASSED tests/test_redmine_client.py::test_get_trackers_success
PASSED tests/test_redmine_client.py::test_get_trackers_auth_failure
PASSED tests/test_redmine_client.py::test_get_trackers_connection_error
PASSED tests/test_redmine_client.py::test_get_trackers_timeout
PASSED tests/test_redmine_client.py::test_get_issue_statuses_success
PASSED tests/test_redmine_client.py::test_get_trackers_missing_env
6 passed
```

### Step 3: Commit

```bash
git add src/redmine_client.py tests/test_redmine_client.py
git commit -m "feat: implement Redmine API client with TDD (get_trackers, get_issue_statuses)"
```

---

## Task 3: Fallback 로직 + Tracker/Status 로더 구현

**Files:**
- Modify: `src/redmine_client.py` (함수 추가)
- Modify: `tests/test_redmine_client.py` (테스트 추가)

### Step 1: 실패하는 Fallback 테스트 추가

`tests/test_redmine_client.py` 하단에 아래 테스트를 추가한다.

```python
def test_load_trackers_fallback_when_no_config():
    from src.redmine_client import load_trackers_with_fallback
    result, is_api = load_trackers_with_fallback("", "")
    assert is_api is False and "Defect" in result

def test_load_trackers_uses_api_when_available():
    from src.redmine_client import load_trackers_with_fallback
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"trackers": [{"id": 1, "name": "Bug"}, {"id": 2, "name": "Task"}]}
    with patch("src.redmine_client.requests.get", return_value=mock_response):
        result, is_api = load_trackers_with_fallback("http://redmine.internal", "key")
    assert is_api is True and "Bug" in result

def test_load_statuses_fallback_when_no_config():
    from src.redmine_client import load_statuses_with_fallback
    result, is_api = load_statuses_with_fallback("", "")
    assert is_api is False and "New" in result
```

### Step 2: 테스트 실행 - 실패 확인

Run: `pytest tests/test_redmine_client.py::test_load_trackers_fallback_when_no_config tests/test_redmine_client.py::test_load_trackers_uses_api_when_available tests/test_redmine_client.py::test_load_statuses_fallback_when_no_config -v`

Expected:
```
FAILED ... ImportError: cannot import name 'load_trackers_with_fallback'
3 failed
```

### Step 3: Fallback 로더 함수 추가

`src/redmine_client.py` 하단에 아래 함수들을 추가한다.

```python
def load_trackers_with_fallback(base_url: str, api_key: str) -> tuple[list[str], bool]:
    """Returns (tracker_names, is_from_api)"""
    if not base_url or not api_key:
        return TRACKER_FALLBACK, False
    trackers, err = get_trackers(base_url, api_key)
    if err or not trackers:
        return TRACKER_FALLBACK, False
    return [t["name"] for t in trackers], True

def load_statuses_with_fallback(base_url: str, api_key: str) -> tuple[list[str], bool]:
    """Returns (status_names, is_from_api)"""
    if not base_url or not api_key:
        return STATUS_FALLBACK, False
    statuses, err = get_issue_statuses(base_url, api_key)
    if err or not statuses:
        return STATUS_FALLBACK, False
    return [s["name"] for s in statuses], True
```

### Step 4: 테스트 실행 - 통과 확인

Run: `pytest tests/test_redmine_client.py -v`

Expected:
```
9 passed
```

### Step 5: Commit

```bash
git add src/redmine_client.py tests/test_redmine_client.py
git commit -m "feat: add load_trackers_with_fallback and load_statuses_with_fallback"
```

---

## Task 4: app.py 드롭다운 교체 (Surgical Change)

**Files:**
- Modify: `app.py` (Tracker/Status selectbox 2곳만 수정, 나머지는 건드리지 않음)

이 태스크가 Sprint 4의 핵심 변경이다. **기존 폼 코드는 한 줄도 변경하지 않는다.**

### Step 1: app.py 상단 임포트에 redmine_client 추가

`app.py` 상단 임포트 섹션에서 아래 줄을 추가한다.

```python
import os
from src.redmine_client import load_trackers_with_fallback, load_statuses_with_fallback
```

### Step 2: 캐싱 함수 추가

임포트 직후에 아래 캐싱 함수를 추가한다 (TTL 5분으로 API 호출 최소화).

```python
@st.cache_data(ttl=300)
def _cached_trackers():
    base_url = os.getenv("REDMINE_BASE_URL", "")
    api_key = os.getenv("REDMINE_API_KEY", "")
    return load_trackers_with_fallback(base_url, api_key)

@st.cache_data(ttl=300)
def _cached_statuses():
    base_url = os.getenv("REDMINE_BASE_URL", "")
    api_key = os.getenv("REDMINE_API_KEY", "")
    return load_statuses_with_fallback(base_url, api_key)
```

### Step 3: 드롭다운 로드 코드 삽입

폼이 렌더링되는 위치에서, Tracker/Status selectbox 직전에 아래 코드를 추가한다.

```python
_tracker_names, _tracker_is_api = _cached_trackers()
_status_names, _status_is_api = _cached_statuses()

if not _tracker_is_api:
    st.caption("⚠️ 연동 설정이 아직 안 되어 있어요. 템플릿 복붙만 사용할 수 있어요.")
```

### Step 4: 기존 Tracker selectbox 교체

기존 코드:
```python
tracker = st.selectbox(
    "Tracker",
    ["Common", "Feature", "Defect", "Request", "Patch", "Issue", "Review"],
)
```

교체 코드:
```python
tracker = st.selectbox("Tracker", _tracker_names)
```

### Step 5: 기존 Status selectbox 교체

기존 코드:
```python
status = st.selectbox(
    "Status",
    ["New", "Confirm", "Assigned", "In progress", "Resolved", "Closed", "Need Feedback", "Rejected"],
    index=0,
)
```

교체 코드:
```python
status = st.selectbox("Status", _status_names, index=0)
```

### Step 6: 수동 확인 - 앱 실행

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속 후:
- Redmine 미설정 시: `⚠️ 연동 설정이 아직 안 되어 있어요. 템플릿 복붙만 사용할 수 있어요.` 메시지 표시 확인
- Tracker/Status 드롭다운에 fallback 값 정상 표시 확인
- 기존 템플릿 생성 버튼 및 Claude 분석 기능 정상 동작 확인 (회귀 없음)

### Step 7: Commit

```bash
git add app.py
git commit -m "feat: replace hardcoded Tracker/Status dropdowns with Redmine API + fallback (surgical change)"
```

---

## Task 5: Redmine 메타데이터 섹션 추가

**Files:**
- Modify: `app.py` (우측 컬럼 하단에 expander 추가)

### Step 1: Redmine 정보 expander 추가

`app.py` 우측 컬럼의 템플릿 출력 영역 아래에 아래 코드를 추가한다.

```python
with st.expander("🔗 Redmine 정보"):
    st.caption("이슈 생성 시 참고하세요")
    # 선택된 Tracker/Status의 이름 표시 (ID는 향후 write 연동 대비)
    st.write(f"선택된 Tracker: **{tracker}**")
    st.write(f"선택된 Status: **{status}**")
```

### Step 2: 수동 확인 - expander 동작

```bash
streamlit run app.py
```

브라우저에서:
1. 우측 컬럼 하단의 "🔗 Redmine 정보" expander 클릭
2. "선택된 Tracker: **Defect**" 형태로 표시 확인
3. 드롭다운에서 다른 값 선택 후 expander 내 값이 연동되어 변경되는지 확인

### Step 3: Commit

```bash
git add app.py
git commit -m "feat: add Redmine metadata expander section in right column"
```

---

## Task 6: 전체 pytest 실행 + 에러 조합 테스트

**Files:**
- Modify: `tests/test_redmine_client.py` (누락 케이스 있을 경우만)

### Step 1: 전체 pytest 실행

Run:
```bash
pytest tests/ -v --tb=short
```

Expected 출력:
```
tests/test_redmine_client.py::test_get_trackers_success           PASSED
tests/test_redmine_client.py::test_get_trackers_auth_failure      PASSED
tests/test_redmine_client.py::test_get_trackers_connection_error  PASSED
tests/test_redmine_client.py::test_get_trackers_timeout           PASSED
tests/test_redmine_client.py::test_get_issue_statuses_success     PASSED
tests/test_redmine_client.py::test_get_trackers_missing_env       PASSED
tests/test_redmine_client.py::test_load_trackers_fallback_when_no_config   PASSED
tests/test_redmine_client.py::test_load_trackers_uses_api_when_available   PASSED
tests/test_redmine_client.py::test_load_statuses_fallback_when_no_config   PASSED
... (기존 Sprint 1~3 테스트 포함)

XX passed in X.XXs
```

실패가 있으면 `--tb=short` 출력을 확인해 수정한다.

### Step 2: 에러 조합 수동 테스트 A - 모든 설정 없음

`.env`에서 `ANTHROPIC_API_KEY`, `REDMINE_BASE_URL`, `REDMINE_API_KEY`를 모두 제거하고 실행:

```bash
streamlit run app.py
```

Expected:
- `⚠️ 연동 설정이 아직 안 되어 있어요.` 메시지 표시
- Tracker/Status 드롭다운에 fallback 값 표시 (Defect, New 포함)
- "버그버디에게 정리 부탁하기" 클릭 시 7개 섹션 템플릿 정상 생성
- 앱 크래시 없음

### Step 3: 에러 조합 수동 테스트 B - Claude만 설정

`ANTHROPIC_API_KEY`만 `.env`에 있는 상태:

Expected:
- 템플릿 생성 정상
- Claude 분석 정상
- Redmine fallback 메시지 표시

### Step 4: Commit (회귀 수정이 있는 경우에만)

```bash
git add tests/
git commit -m "test: add missing edge case tests for redmine_client"
```

---

## Task 7: README.md 작성

**Files:**
- Create: `README.md`

### Step 1: README.md 작성

`README.md`를 생성한다.

```markdown
# 버그버디 (BugBuddy)

사업팀/운영팀의 레드마인 이슈를 구조화하고, 개발자가 어디를 먼저 봐야 할지 빠르게 파악하도록 돕는 내부용 도구

## 설치

```bash
pip install -r requirements.txt
```

## 환경 설정

`.env.example`을 복사해 `.env`를 만들고 값을 채운다.

```bash
cp .env.example .env
```

`.env` 설정 항목:

```
# Claude API 키 (https://console.anthropic.com 에서 발급)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Redmine 연동 (선택 사항 - 미설정 시 기본값 사용)
REDMINE_BASE_URL=https://your-redmine.internal
REDMINE_API_KEY=your_redmine_api_key_here
REDMINE_PROJECT_ID=your_project_id
```

## customers.json 작성

`data/customers.json`에 고객사별 코드 레포 정보를 작성한다.

스키마:

```json
[
  {
    "id": "customer-id",
    "name": "고객사명",
    "source_targets": [
      {
        "label": "표시 레이블 (고객사명 + 브랜치)",
        "repo_url": "https://git.internal/repo.git",
        "branch": "main",
        "local_path": "/home/dev/repos/customer-repo",
        "paths": ["front-end/", "back-end/"],
        "priority": 1
      }
    ]
  }
]
```

`local_path`는 버그버디를 실행하는 머신에서 실제로 레포가 클론된 경로를 입력한다.

## 실행

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속

## 주요 기능

1. **이슈 템플릿 생성**: 입력 폼 → 레드마인 Description 7개 섹션 자동 구성 + 원클릭 복사
2. **Claude 분석**: 누락 필드 탐지, 추가 질문 생성, 추천 제목/Description 제시
3. **코드 후보 검색**: 고객사별 로컬 레포에서 키워드 기반 Top-N 관련 파일 추천

## 주의 사항

- 환자명, 주민번호 등 PII/PHI는 입력하지 마세요. 내부 ID나 마스킹된 값을 사용하세요.
- `ANTHROPIC_API_KEY` 미설정 시 Claude 분석 기능은 사용할 수 없지만 템플릿 생성은 정상 동작합니다.
- `REDMINE_BASE_URL` 미설정 시 Tracker/Status 기본값이 사용됩니다.
```

### Step 2: Commit

```bash
git add README.md
git commit -m "docs: add README with installation, config, and usage guide"
```

---

## Task 8: v1 태그 생성

**Files:**
- (파일 변경 없음)

### Step 1: 전체 테스트 최종 확인

```bash
pytest tests/ -v --tb=short
```

Expected: 전체 PASSED, 실패 없음

### Step 2: 최종 커밋 및 v1 태그

```bash
git add .
git commit -m "feat: v1 release - Redmine integration + full feature integration"
git tag -a v1.0.0 -m "버그버디 v1 릴리스"
```

### Step 3: 태그 확인

```bash
git tag -l
git show v1.0.0 --stat
```

Expected:
```
v1.0.0
tag v1.0.0
Tagger: ...
Date: ...
버그버디 v1 릴리스
...
```

---

## Task 9: Playwright MCP 전체 E2E 검증

**전제 조건:** `streamlit run app.py` 실행 중 (`http://localhost:8501`)

### 시나리오 A: Redmine 미설정 Fallback 확인

```
1. browser_navigate → http://localhost:8501
2. browser_snapshot → "연동 설정이 아직 안 되어 있어요" 메시지 확인
3. browser_snapshot → Tracker 드롭다운에 "Defect" 포함 확인
4. browser_snapshot → Status 드롭다운에 "New" 포함 확인
5. browser_click → "🔗 Redmine 정보" expander 펼치기
6. browser_snapshot → "선택된 Tracker", "선택된 Status" 텍스트 확인
```

### 시나리오 B: 전체 End-to-End 플로우

```
1. browser_navigate → http://localhost:8501
2. browser_select_option → Tracker = "Defect" 선택
3. browser_select_option → Status = "New" 선택
4. browser_type → 메뉴명 필드에 "주문관리" 입력
5. browser_type → 에러 내용 필드에 "주문 등록 시 500 에러 발생" 입력
6. browser_type → 재현 절차 필드에 "1. 주문 메뉴 이동 2. 고객사 선택 3. 저장 클릭" 입력
7. browser_click → "버그버디에게 정리 부탁하기"
8. browser_wait_for → "(1) 에러 내용" 텍스트 출현 대기
9. browser_snapshot → 7개 섹션 템플릿 확인
10. browser_click → "추가로 뭐가 더 필요할지 물어보기"
11. browser_wait_for → Claude 분석 결과 출현 대기 (최대 15초)
12. browser_snapshot → 추천 제목/Description/질문 리스트 확인
13. browser_click → "추천 코드 확인하기"
14. browser_wait_for → 코드 후보 결과 또는 "찾지 못했어요" 메시지
15. browser_console_messages(level: "error") → 콘솔 에러 없음 확인
```

### 시나리오 C: 에러 상태 시나리오 (Claude 키 없음 + Redmine 없음 + customers.json 없음)

```
(.env에서 모든 키 제거, data/customers.json 임시 rename 후 앱 재시작)
1. browser_navigate → http://localhost:8501
2. browser_snapshot → 기본 템플릿 생성 폼 정상 표시 확인
3. browser_click → "버그버디에게 정리 부탁하기"
4. browser_wait_for → 7개 섹션 템플릿 정상 생성 확인
5. browser_snapshot → 앱 크래시 없음, 오류 화면 없음 확인
```

---

## Sprint 4 완료 기준 체크리스트

```
Redmine 연동:
[ ] REDMINE_BASE_URL + REDMINE_API_KEY 설정 시 API 기반 Tracker/Status 드롭다운 동작
[ ] @st.cache_data(ttl=300)으로 API 호출 5분 캐싱

Fallback:
[ ] REDMINE_BASE_URL 미설정 시 하드코딩 fallback + "연동 설정이 아직 안 되어 있어요" 메시지
[ ] API 호출 실패(401/타임아웃/연결 오류) 시 동일 fallback
[ ] 앱 크래시 없음

메타데이터 섹션:
[ ] "🔗 Redmine 정보" expander에서 선택된 Tracker/Status 이름 표시
[ ] create_issue stub 함수 (NotImplementedError 포함)

통합:
[ ] pytest tests/ -v 전체 PASSED
[ ] 에러 조합 3가지 시나리오 모두 앱 크래시 없음
[ ] 기존 Sprint 1~3 기능 회귀 없음

문서:
[ ] README.md에 설치/설정/실행/주요 기능 포함
[ ] git tag v1.0.0 생성 완료
```
