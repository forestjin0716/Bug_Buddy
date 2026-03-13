# Sprint 4: Redmine 연동 + 통합 폴리시 구현 계획

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redmine REST API에서 Tracker/Status 메타데이터를 읽어와 드롭다운을 동적으로 구성하고, 전체 기능을 통합 점검하여 v1을 릴리스한다.

**Architecture:** `src/redmine_client.py`가 Redmine REST API를 read-only로 호출하여 Tracker/Status 목록을 반환한다. `app.py`는 API 성공 시 동적 목록을, 실패 또는 미설정 시 Sprint 1의 하드코딩 fallback을 사용한다. Karpathy Surgical Changes 원칙에 따라 기존 코드는 드롭다운 교체 부분만 수정하고 나머지는 건드리지 않는다.

**Tech Stack:** Python 3.x, Streamlit, `requests`, `python-dotenv`, `pytest`, `unittest.mock`

**스프린트 정보:**
- 기간: 2026-05-01 ~ 2026-05-15 (2주)
- MoSCoW: Should Have (PRD 5.4)
- 마일스톤: M4 - v1 릴리스
- Karpathy Guideline: Surgical Changes (하드코딩된 목록 → API 응답 교체만, 기존 코드 최소 변경)
- 의존성: Sprint 1~3 완료 필요

---

## Fallback 하드코딩 값 (전체 스프린트 기준값)

Redmine API 미설정 또는 호출 실패 시 아래 값을 사용한다.

```python
FALLBACK_TRACKERS = [
    {"id": 1, "name": "Common"},
    {"id": 2, "name": "Feature"},
    {"id": 3, "name": "Defect"},
    {"id": 4, "name": "Request"},
    {"id": 5, "name": "Patch"},
    {"id": 6, "name": "Issue"},
    {"id": 7, "name": "Review"},
]

FALLBACK_STATUSES = [
    {"id": 1, "name": "New"},
    {"id": 2, "name": "Confirm"},
    {"id": 3, "name": "Assigned"},
    {"id": 4, "name": "In progress"},
    {"id": 5, "name": "Resolved"},
    {"id": 6, "name": "Closed"},
    {"id": 7, "name": "Need Feedback"},
    {"id": 8, "name": "Rejected"},
]
```

---

## Task 1: 프로젝트 구조 준비 및 의존성 확인

**Files:**
- Modify: `requirements.txt`
- Create: `src/redmine_client.py` (빈 파일)
- Create: `tests/test_redmine_client.py` (빈 파일)

### Step 1: requirements.txt에 requests 패키지 확인

`requirements.txt`에 아래 패키지가 모두 있는지 확인하고, 없으면 추가한다.

```
streamlit
anthropic
python-dotenv
requests
pytest
```

### Step 2: 파일 생성

```bash
touch src/redmine_client.py tests/test_redmine_client.py
```

### Step 3: 의존성 설치 확인

```bash
pip install -r requirements.txt
```

Expected: `Requirement already satisfied` 또는 `Successfully installed requests-...`

### Step 4: requests 임포트 동작 확인

```bash
python -c "import requests; print('requests OK', requests.__version__)"
```

Expected: `requests OK 2.x.x`

### Step 5: Commit

```bash
git add requirements.txt src/redmine_client.py tests/test_redmine_client.py
git commit -m "chore: scaffold redmine_client files and confirm requests dependency"
```

---

## Task 2: Redmine API 클라이언트 구현 (TDD)

**Files:**
- Modify: `src/redmine_client.py`
- Modify: `tests/test_redmine_client.py`

이 태스크는 Mock HTTP 응답을 사용하여 실제 Redmine 서버 없이 테스트한다.

### Step 1: 실패하는 테스트 작성

`tests/test_redmine_client.py`에 아래 내용을 작성한다.

```python
import pytest
from unittest.mock import MagicMock, patch
from src.redmine_client import (
    get_trackers,
    get_issue_statuses,
    FALLBACK_TRACKERS,
    FALLBACK_STATUSES,
)


class TestGetTrackers:
    """get_trackers() 테스트 (Mock HTTP 사용)"""

    def _make_mock_response(self, json_data: dict, status_code: int = 200):
        """requests.get 응답 Mock 생성 헬퍼"""
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_resp.json.return_value = json_data
        mock_resp.raise_for_status.return_value = None
        if status_code >= 400:
            import requests
            mock_resp.raise_for_status.side_effect = requests.HTTPError(
                response=mock_resp
            )
        return mock_resp

    def test_valid_response_returns_tracker_list(self):
        """정상 응답 시 Tracker 목록을 반환한다"""
        mock_resp = self._make_mock_response({
            "trackers": [
                {"id": 1, "name": "Common"},
                {"id": 3, "name": "Defect"},
            ]
        })

        with patch("src.redmine_client.requests.get", return_value=mock_resp):
            with patch.dict("os.environ", {
                "REDMINE_BASE_URL": "https://redmine.internal",
                "REDMINE_API_KEY": "test-api-key",
            }):
                result = get_trackers()

        assert result is not None
        assert len(result) == 2
        assert result[0] == {"id": 1, "name": "Common"}
        assert result[1] == {"id": 3, "name": "Defect"}

    def test_request_uses_correct_headers_and_url(self):
        """GET 요청에 X-Redmine-API-Key 헤더와 올바른 URL을 사용한다"""
        mock_resp = self._make_mock_response({"trackers": []})

        with patch("src.redmine_client.requests.get", return_value=mock_resp) as mock_get:
            with patch.dict("os.environ", {
                "REDMINE_BASE_URL": "https://redmine.internal",
                "REDMINE_API_KEY": "my-secret-key",
            }):
                get_trackers()

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "https://redmine.internal/trackers.json" in call_args[0]
        assert call_args[1]["headers"]["X-Redmine-API-Key"] == "my-secret-key"
        assert call_args[1]["timeout"] == 5

    def test_auth_failure_returns_none(self):
        """인증 실패(401) 시 None을 반환한다"""
        mock_resp = self._make_mock_response({}, status_code=401)

        with patch("src.redmine_client.requests.get", return_value=mock_resp):
            with patch.dict("os.environ", {
                "REDMINE_BASE_URL": "https://redmine.internal",
                "REDMINE_API_KEY": "wrong-key",
            }):
                result = get_trackers()

        assert result is None

    def test_timeout_returns_none(self):
        """타임아웃 발생 시 None을 반환한다"""
        import requests as req_lib

        with patch("src.redmine_client.requests.get",
                   side_effect=req_lib.Timeout("Connection timed out")):
            with patch.dict("os.environ", {
                "REDMINE_BASE_URL": "https://redmine.internal",
                "REDMINE_API_KEY": "test-api-key",
            }):
                result = get_trackers()

        assert result is None

    def test_connection_error_returns_none(self):
        """연결 실패 시 None을 반환한다"""
        import requests as req_lib

        with patch("src.redmine_client.requests.get",
                   side_effect=req_lib.ConnectionError("Connection refused")):
            with patch.dict("os.environ", {
                "REDMINE_BASE_URL": "https://redmine.internal",
                "REDMINE_API_KEY": "test-api-key",
            }):
                result = get_trackers()

        assert result is None

    def test_env_not_set_returns_none(self):
        """환경변수 미설정 시 None을 반환한다"""
        import os
        env = {k: v for k, v in os.environ.items()
               if k not in ("REDMINE_BASE_URL", "REDMINE_API_KEY")}

        with patch.dict("os.environ", env, clear=True):
            result = get_trackers()

        assert result is None

    def test_base_url_only_returns_none(self):
        """REDMINE_BASE_URL만 설정하고 API_KEY 미설정 시 None을 반환한다"""
        import os
        env = {k: v for k, v in os.environ.items() if k != "REDMINE_API_KEY"}
        env["REDMINE_BASE_URL"] = "https://redmine.internal"

        with patch.dict("os.environ", env, clear=True):
            result = get_trackers()

        assert result is None


class TestGetIssueStatuses:
    """get_issue_statuses() 테스트 (Mock HTTP 사용)"""

    def _make_mock_response(self, json_data: dict, status_code: int = 200):
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_resp.json.return_value = json_data
        mock_resp.raise_for_status.return_value = None
        if status_code >= 400:
            import requests
            mock_resp.raise_for_status.side_effect = requests.HTTPError(
                response=mock_resp
            )
        return mock_resp

    def test_valid_response_returns_status_list(self):
        """정상 응답 시 Status 목록을 반환한다"""
        mock_resp = self._make_mock_response({
            "issue_statuses": [
                {"id": 1, "name": "New"},
                {"id": 2, "name": "Confirm"},
                {"id": 5, "name": "Resolved"},
            ]
        })

        with patch("src.redmine_client.requests.get", return_value=mock_resp):
            with patch.dict("os.environ", {
                "REDMINE_BASE_URL": "https://redmine.internal",
                "REDMINE_API_KEY": "test-api-key",
            }):
                result = get_issue_statuses()

        assert result is not None
        assert len(result) == 3
        assert result[0] == {"id": 1, "name": "New"}

    def test_request_uses_correct_url(self):
        """GET 요청이 /issue_statuses.json 엔드포인트를 사용한다"""
        mock_resp = self._make_mock_response({"issue_statuses": []})

        with patch("src.redmine_client.requests.get", return_value=mock_resp) as mock_get:
            with patch.dict("os.environ", {
                "REDMINE_BASE_URL": "https://redmine.internal",
                "REDMINE_API_KEY": "test-api-key",
            }):
                get_issue_statuses()

        call_args = mock_get.call_args
        assert "https://redmine.internal/issue_statuses.json" in call_args[0]

    def test_timeout_returns_none(self):
        """타임아웃 시 None을 반환한다"""
        import requests as req_lib

        with patch("src.redmine_client.requests.get",
                   side_effect=req_lib.Timeout("timed out")):
            with patch.dict("os.environ", {
                "REDMINE_BASE_URL": "https://redmine.internal",
                "REDMINE_API_KEY": "test-api-key",
            }):
                result = get_issue_statuses()

        assert result is None

    def test_auth_failure_returns_none(self):
        """인증 실패(401) 시 None을 반환한다"""
        mock_resp = self._make_mock_response({}, status_code=401)

        with patch("src.redmine_client.requests.get", return_value=mock_resp):
            with patch.dict("os.environ", {
                "REDMINE_BASE_URL": "https://redmine.internal",
                "REDMINE_API_KEY": "bad-key",
            }):
                result = get_issue_statuses()

        assert result is None

    def test_env_not_set_returns_none(self):
        """환경변수 미설정 시 None을 반환한다"""
        import os
        env = {k: v for k, v in os.environ.items()
               if k not in ("REDMINE_BASE_URL", "REDMINE_API_KEY")}

        with patch.dict("os.environ", env, clear=True):
            result = get_issue_statuses()

        assert result is None


class TestFallbackConstants:
    """Fallback 상수 구조 검증"""

    def test_fallback_trackers_have_id_and_name(self):
        """FALLBACK_TRACKERS의 각 항목은 id와 name을 가진다"""
        for item in FALLBACK_TRACKERS:
            assert "id" in item
            assert "name" in item
            assert isinstance(item["id"], int)
            assert isinstance(item["name"], str)

    def test_fallback_statuses_have_id_and_name(self):
        """FALLBACK_STATUSES의 각 항목은 id와 name을 가진다"""
        for item in FALLBACK_STATUSES:
            assert "id" in item
            assert "name" in item

    def test_fallback_trackers_contains_defect(self):
        """FALLBACK_TRACKERS에 Defect이 포함된다"""
        names = [t["name"] for t in FALLBACK_TRACKERS]
        assert "Defect" in names

    def test_fallback_statuses_contains_new(self):
        """FALLBACK_STATUSES에 New가 포함된다"""
        names = [s["name"] for s in FALLBACK_STATUSES]
        assert "New" in names
```

### Step 2: 테스트 실행 - 실패 확인

```bash
pytest tests/test_redmine_client.py -v
```

Expected: `ImportError` 또는 `ModuleNotFoundError` (아직 구현 없음)

### Step 3: Redmine 클라이언트 구현

`src/redmine_client.py`에 아래 내용을 작성한다.

```python
"""
Redmine REST API 클라이언트 (read-only)

환경변수에서 REDMINE_BASE_URL과 REDMINE_API_KEY를 읽어
Tracker 목록과 Issue Status 목록을 반환한다.

미설정 또는 호출 실패 시 None을 반환하며,
호출 측에서 FALLBACK_TRACKERS / FALLBACK_STATUSES로 대체해야 한다.
"""
from __future__ import annotations

import os
import requests

# ──────────────────────────────────────────────
# Fallback 하드코딩 값 (Redmine 미설정 또는 API 실패 시 사용)
# ──────────────────────────────────────────────
FALLBACK_TRACKERS: list[dict] = [
    {"id": 1, "name": "Common"},
    {"id": 2, "name": "Feature"},
    {"id": 3, "name": "Defect"},
    {"id": 4, "name": "Request"},
    {"id": 5, "name": "Patch"},
    {"id": 6, "name": "Issue"},
    {"id": 7, "name": "Review"},
]

FALLBACK_STATUSES: list[dict] = [
    {"id": 1, "name": "New"},
    {"id": 2, "name": "Confirm"},
    {"id": 3, "name": "Assigned"},
    {"id": 4, "name": "In progress"},
    {"id": 5, "name": "Resolved"},
    {"id": 6, "name": "Closed"},
    {"id": 7, "name": "Need Feedback"},
    {"id": 8, "name": "Rejected"},
]

_TIMEOUT_SECONDS = 5


def _get_credentials() -> tuple[str, str] | tuple[None, None]:
    """
    환경변수에서 Redmine 접속 정보를 읽는다.

    Returns:
        (base_url, api_key) 또는 미설정 시 (None, None)
    """
    base_url = os.environ.get("REDMINE_BASE_URL", "").rstrip("/")
    api_key = os.environ.get("REDMINE_API_KEY", "")
    if not base_url or not api_key:
        return None, None
    return base_url, api_key


def _get(url: str, api_key: str) -> requests.Response | None:
    """
    GET 요청을 보내고 응답을 반환한다.
    연결 실패/타임아웃/HTTP 에러 시 None을 반환한다.
    """
    try:
        response = requests.get(
            url,
            headers={"X-Redmine-API-Key": api_key},
            timeout=_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response
    except (requests.Timeout, requests.ConnectionError, requests.HTTPError):
        return None


def get_trackers() -> list[dict] | None:
    """
    Redmine GET /trackers.json 을 호출하여 Tracker 목록을 반환한다.

    Returns:
        [{"id": int, "name": str}, ...] 또는 실패/미설정 시 None
    """
    base_url, api_key = _get_credentials()
    if base_url is None:
        return None

    response = _get(f"{base_url}/trackers.json", api_key)
    if response is None:
        return None

    return response.json().get("trackers", [])


def get_issue_statuses() -> list[dict] | None:
    """
    Redmine GET /issue_statuses.json 을 호출하여 Status 목록을 반환한다.

    Returns:
        [{"id": int, "name": str}, ...] 또는 실패/미설정 시 None
    """
    base_url, api_key = _get_credentials()
    if base_url is None:
        return None

    response = _get(f"{base_url}/issue_statuses.json", api_key)
    if response is None:
        return None

    return response.json().get("issue_statuses", [])


def create_issue(
    project_id: str,
    tracker_id: int,
    status_id: int,
    subject: str,
    description: str,
) -> None:
    """
    Redmine 이슈 생성 (v2에서 구현 예정).

    Args:
        project_id: Redmine 프로젝트 식별자
        tracker_id: Tracker ID
        status_id: Status ID
        subject: 이슈 제목
        description: 이슈 내용

    Raises:
        NotImplementedError: v2에서 구현 예정
    """
    raise NotImplementedError("v2에서 구현 예정")
```

### Step 4: 테스트 실행 - 통과 확인

```bash
pytest tests/test_redmine_client.py -v
```

Expected: 전체 테스트 PASS (TestGetTrackers 7개 + TestGetIssueStatuses 5개 + TestFallbackConstants 4개 = 16개)

### Step 5: Commit

```bash
git add src/redmine_client.py tests/test_redmine_client.py
git commit -m "feat: implement Redmine API client with fallback constants (TDD)"
```

---

## Task 3: Redmine 미설정 Fallback 로직 및 안내 메시지 구현

**Files:**
- Create: `src/redmine_config.py`
- Modify: `tests/test_redmine_client.py`

이 태스크는 `app.py`에서 호출하는 단일 진입점 함수를 만든다. API 성공 시 API 값, 실패 시 fallback 값을 반환하고, 미설정 여부를 알리는 플래그를 포함한다.

### Step 1: 실패하는 테스트 작성

`tests/test_redmine_client.py` 하단에 아래 테스트 클래스를 추가한다.

```python
from src.redmine_config import get_tracker_options, get_status_options


class TestGetTrackerOptions:
    """get_tracker_options() - app.py가 직접 호출하는 통합 함수 테스트"""

    def test_api_success_returns_api_values(self):
        """API 호출 성공 시 API 기반 목록과 connected=True를 반환한다"""
        api_trackers = [{"id": 10, "name": "Bug"}, {"id": 11, "name": "Task"}]

        with patch("src.redmine_config.get_trackers", return_value=api_trackers):
            result = get_tracker_options()

        assert result["connected"] is True
        assert result["trackers"] == api_trackers
        assert result["message"] == ""

    def test_api_failure_returns_fallback(self):
        """API 호출 실패(None 반환) 시 fallback 목록을 반환한다"""
        with patch("src.redmine_config.get_trackers", return_value=None):
            result = get_tracker_options()

        assert result["connected"] is False
        assert len(result["trackers"]) > 0
        # fallback은 Defect을 포함해야 한다
        names = [t["name"] for t in result["trackers"]]
        assert "Defect" in names
        assert "연동 설정이 아직 안 되어 있어요" in result["message"]

    def test_api_success_with_empty_list_returns_fallback(self):
        """API가 빈 목록을 반환하면 fallback을 사용한다"""
        with patch("src.redmine_config.get_trackers", return_value=[]):
            result = get_tracker_options()

        assert result["connected"] is False
        assert len(result["trackers"]) > 0


class TestGetStatusOptions:
    """get_status_options() 테스트"""

    def test_api_success_returns_api_values(self):
        """API 호출 성공 시 API 기반 Status 목록을 반환한다"""
        api_statuses = [{"id": 1, "name": "Open"}, {"id": 2, "name": "Closed"}]

        with patch("src.redmine_config.get_issue_statuses", return_value=api_statuses):
            result = get_status_options()

        assert result["connected"] is True
        assert result["statuses"] == api_statuses

    def test_api_failure_returns_fallback(self):
        """API 실패 시 fallback Status 목록을 반환한다"""
        with patch("src.redmine_config.get_issue_statuses", return_value=None):
            result = get_status_options()

        assert result["connected"] is False
        names = [s["name"] for s in result["statuses"]]
        assert "New" in names
```

### Step 2: 테스트 실행 - 실패 확인

```bash
pytest tests/test_redmine_client.py::TestGetTrackerOptions tests/test_redmine_client.py::TestGetStatusOptions -v
```

Expected: `ImportError` - `src.redmine_config` 미정의

### Step 3: redmine_config.py 구현

`src/redmine_config.py`를 새로 생성한다.

```python
"""
Redmine 연동 설정 헬퍼

app.py가 Tracker/Status 드롭다운을 구성할 때 직접 호출하는 단일 진입점.
API 성공 시 API 기반 목록, 실패/미설정 시 fallback 목록을 반환한다.
"""
from __future__ import annotations

from src.redmine_client import (
    get_trackers,
    get_issue_statuses,
    FALLBACK_TRACKERS,
    FALLBACK_STATUSES,
)

_FALLBACK_MESSAGE = (
    "연동 설정이 아직 안 되어 있어요. 템플릿 복붙만 사용할 수 있어요."
)


def get_tracker_options() -> dict:
    """
    Tracker 드롭다운용 데이터를 반환한다.

    Returns:
        {
            "connected": bool,       # API 연결 성공 여부
            "trackers": list[dict],  # [{"id": int, "name": str}, ...]
            "message": str,          # 미연동 시 안내 메시지 (연결 성공 시 빈 문자열)
        }
    """
    trackers = get_trackers()
    if trackers:
        return {"connected": True, "trackers": trackers, "message": ""}
    return {
        "connected": False,
        "trackers": FALLBACK_TRACKERS,
        "message": _FALLBACK_MESSAGE,
    }


def get_status_options() -> dict:
    """
    Status 드롭다운용 데이터를 반환한다.

    Returns:
        {
            "connected": bool,
            "statuses": list[dict],  # [{"id": int, "name": str}, ...]
            "message": str,
        }
    """
    statuses = get_issue_statuses()
    if statuses:
        return {"connected": True, "statuses": statuses, "message": ""}
    return {
        "connected": False,
        "statuses": FALLBACK_STATUSES,
        "message": _FALLBACK_MESSAGE,
    }
```

### Step 4: 테스트 실행 - 통과 확인

```bash
pytest tests/test_redmine_client.py -v
```

Expected: 전체 테스트 PASS (기존 16개 + 신규 5개 = 21개)

### Step 5: Commit

```bash
git add src/redmine_config.py tests/test_redmine_client.py
git commit -m "feat: add redmine_config helper with fallback logic and UX message"
```

---

## Task 4: Phase 1 드롭다운을 API 응답으로 교체

**Files:**
- Modify: `app.py` (Tracker, Status 드롭다운 부분만 수정 - Surgical Change)

이 태스크가 Sprint 4의 핵심 변경이다. `app.py`에서 Tracker와 Status 드롭다운을 구성하는 코드만 수정하고 나머지는 건드리지 않는다.

### Step 1: app.py 상단 임포트에 redmine_config 추가

`app.py` 상단 임포트 섹션에서 아래 줄을 추가한다.

```python
from src.redmine_config import get_tracker_options, get_status_options
```

### Step 2: Streamlit 캐싱으로 API 호출 최소화

`app.py`에서 임포트 직후에 아래 캐싱 함수를 추가한다 (TTL 5분).

```python
@st.cache_data(ttl=300)
def _cached_tracker_options():
    return get_tracker_options()


@st.cache_data(ttl=300)
def _cached_status_options():
    return get_status_options()
```

### Step 3: Redmine 연동 상태 표시

앱 초기화 섹션(레이아웃 구성 직후)에 아래 코드를 추가한다.

```python
# Redmine 연동 상태 확인 (캐싱 적용)
_tracker_opts = _cached_tracker_options()
_status_opts = _cached_status_options()

# 미연동 안내 (두 중 하나라도 미연동이면 한 번만 표시)
if not _tracker_opts["connected"]:
    st.info(_tracker_opts["message"])
```

### Step 4: Tracker 드롭다운 교체

기존 Tracker 드롭다운 코드를 아래로 교체한다.

기존 코드 (Sprint 1에서 작성된 형태):
```python
tracker = st.selectbox(
    "Tracker",
    ["Common", "Feature", "Defect", "Request", "Patch", "Issue", "Review"],
)
```

교체 코드:
```python
_tracker_names = [t["name"] for t in _tracker_opts["trackers"]]
_tracker_ids = [t["id"] for t in _tracker_opts["trackers"]]

_tracker_idx = st.selectbox(
    "Tracker",
    options=range(len(_tracker_names)),
    format_func=lambda i: _tracker_names[i],
    key="tracker_select",
)
tracker = _tracker_names[_tracker_idx]
tracker_id = _tracker_ids[_tracker_idx]   # 내부 ID 보관 (향후 이슈 생성 대비)
st.session_state["tracker"] = tracker
st.session_state["tracker_id"] = tracker_id
```

### Step 5: Status 드롭다운 교체

기존 Status 드롭다운 코드를 아래로 교체한다.

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
_status_names = [s["name"] for s in _status_opts["statuses"]]
_status_ids = [s["id"] for s in _status_opts["statuses"]]

_status_idx = st.selectbox(
    "Status",
    options=range(len(_status_names)),
    format_func=lambda i: _status_names[i],
    index=0,
    key="status_select",
)
status = _status_names[_status_idx]
status_id = _status_ids[_status_idx]   # 내부 ID 보관
st.session_state["status"] = status
st.session_state["status_id"] = status_id
```

### Step 6: 앱 실행 수동 확인

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속 후:
- Redmine 설정이 없는 경우: `st.info`로 "연동 설정이 아직 안 되어 있어요" 메시지 표시 확인
- Tracker/Status 드롭다운에 하드코딩 fallback 값 표시 확인
- 기존 템플릿 생성 기능 정상 동작 확인

### Step 7: Commit

```bash
git add app.py
git commit -m "feat: replace hardcoded Tracker/Status dropdowns with Redmine API (w/ fallback)"
```

---

## Task 5: Redmine 메타데이터 표시 섹션 구현

**Files:**
- Modify: `app.py` (우측 영역에 "Redmine 정보" 섹션 추가)

### Step 1: "Redmine 정보" 섹션 추가

`app.py` 우측 컬럼에서 템플릿 출력 영역 아래에 아래 코드를 추가한다.

```python
# ──────────────────────────────────────────────
# Redmine 메타데이터 표시 섹션 (접기/펼치기)
# ──────────────────────────────────────────────
with st.expander("Redmine 정보"):
    if _tracker_opts["connected"]:
        st.markdown("**선택된 Tracker:**")
        selected_tracker_id = st.session_state.get("tracker_id", "")
        selected_tracker_name = st.session_state.get("tracker", "")
        st.markdown(f"- 이름: `{selected_tracker_name}`")
        st.markdown(f"- ID: `{selected_tracker_id}`")

        st.markdown("**선택된 Status:**")
        selected_status_id = st.session_state.get("status_id", "")
        selected_status_name = st.session_state.get("status", "")
        st.markdown(f"- 이름: `{selected_status_name}`")
        st.markdown(f"- ID: `{selected_status_id}`")

        st.caption("이슈 생성 시 참고하세요.")
    else:
        st.info("Redmine이 연동되지 않아 메타데이터를 표시할 수 없어요.")
```

### Step 2: 앱 실행 수동 확인

```bash
streamlit run app.py
```

브라우저에서:
1. "Redmine 정보" expander 클릭
2. Redmine 연동 시: Tracker/Status 이름과 ID 표시 확인
3. Redmine 미연동 시: 안내 메시지 표시 확인

### Step 3: Commit

```bash
git add app.py
git commit -m "feat: add Redmine metadata display section (expander)"
```

---

## Task 6: 전체 통합 테스트 및 UI 폴리시

**Files:**
- Modify: `app.py` (문구, 레이아웃 일관성 수정)

이 태스크는 자동화 테스트가 아닌 수동 점검이다.

### Step 1: 에러 조합 테스트 시나리오

아래 3가지 조합을 순서대로 테스트한다.

**시나리오 A: 모든 설정 없음**

`.env`에서 `ANTHROPIC_API_KEY`, `REDMINE_BASE_URL`, `REDMINE_API_KEY`를 모두 제거한다. `data/customers.json`을 임시로 이름 변경한다.

```bash
streamlit run app.py
```

Expected:
- API 키 미설정 경고 표시 (사이드바 또는 상단)
- "연동 설정이 아직 안 되어 있어요" 안내 메시지 표시
- Tracker/Status 하드코딩 값으로 드롭다운 표시
- "버그버디에게 정리 부탁하기" 클릭 시 7개 섹션 템플릿 정상 생성
- 앱 크래시 없음

**시나리오 B: Claude만 설정, Redmine 미설정**

`ANTHROPIC_API_KEY`만 복원한다.

Expected:
- 템플릿 생성 정상
- Claude 분석 정상
- Redmine fallback 메시지 표시
- 코드 검색 정상 (customers.json 있는 경우)

**시나리오 C: 모든 설정 완료**

모든 환경변수 복원.

Expected:
- Tracker/Status 드롭다운에 Redmine API 기반 목록 표시
- "Redmine 정보" expander에서 ID + 이름 확인
- 전체 플로우 정상

### Step 2: UI 일관성 점검 체크리스트

아래 항목을 수동으로 점검하고, 일관성 없는 부분은 `app.py`에서 수정한다.

```
버튼 문구:
[ ] "버그버디에게 정리 부탁하기" - 입력 폼 하단
[ ] "추가로 뭐가 더 필요할지 물어보기" - 템플릿 생성 후 활성화
[ ] "추천 코드 확인하기" - 코드 후보 검색

에러 메시지 톤:
[ ] 모든 에러 메시지가 친근한 한국어 ("...이에요", "...해주세요")
[ ] st.error / st.warning / st.info 레벨 적절 사용

로딩 메시지:
[ ] "버그버디가 분석하고 있어요..." - Claude 분석 중
[ ] "버그버디가 코드를 찾고 있어요..." - 코드 검색 중
```

### Step 3: Commit (수정 사항이 있는 경우)

```bash
git add app.py
git commit -m "polish: align all button/error/loading messages to BugBuddy tone"
```

---

## Task 7: Playwright MCP 검증

**전제 조건:** `streamlit run app.py` 실행 중

이 태스크는 Playwright MCP를 통한 브라우저 자동화 검증이다.

### 시나리오 A: Redmine 연동 정상 흐름 (유효한 REDMINE 설정 필요)

```
1. browser_navigate → http://localhost:8501
2. browser_snapshot → Tracker 드롭다운에 Redmine API 기반 목록 표시 확인
3. browser_snapshot → Status 드롭다운에 Redmine API 기반 목록 표시 확인
4. browser_select_option → Tracker 선택
5. browser_select_option → Status 선택
6. browser_click → "Redmine 정보" expander 펼치기
7. browser_snapshot → 선택한 Tracker/Status의 ID와 이름 표시 확인
8. browser_network_requests → /trackers.json, /issue_statuses.json 호출 200 확인
```

### 시나리오 B: Redmine 미설정 Fallback

```
(.env에서 REDMINE_BASE_URL 제거 후 앱 재시작)
1. browser_navigate → http://localhost:8501
2. browser_snapshot → "연동 설정이 아직 안 되어 있어요" 메시지 확인
3. browser_snapshot → Tracker/Status 드롭다운에 하드코딩 값 표시 확인
4. browser_select_option → Tracker = "Defect" 선택
5. browser_click → "버그버디에게 정리 부탁하기"
6. browser_wait_for → 템플릿 정상 생성 확인 (앱 크래시 없음)
```

### 시나리오 C: 전체 End-to-End 플로우

```
1. browser_navigate → http://localhost:8501
2. browser_select_option → Tracker, Status, Priority, Category, 고객사 모두 선택
3. browser_type → 메뉴명 필드에 "주문관리" 입력
4. browser_type → 에러 내용 필드에 "주문 등록 시 500 에러 발생" 입력
5. browser_type → 재현 절차 필드에 "1. 주문 메뉴 이동 2. 고객사 선택 3. 저장 클릭" 입력
6. browser_click → "버그버디에게 정리 부탁하기"
7. browser_wait_for → "(1) 에러 내용" 텍스트 출현 대기
8. browser_snapshot → 7개 섹션 템플릿 확인
9. browser_click → "추가로 뭐가 더 필요할지 물어보기"
10. browser_wait_for → "버그버디가 분석하고 있어요" 로딩 표시
11. browser_wait_for → "추천 제목" 텍스트 출현 대기 (최대 15초)
12. browser_snapshot → 추천 제목/Description/질문 리스트/리스크 플래그 확인
13. browser_select_option → 코드 후보 검색 고객사/소스 타겟 선택
14. browser_type → 키워드1 필드에 "주문관리" 입력
15. browser_click → "추천 코드 확인하기"
16. browser_wait_for → 코드 후보 결과 또는 "찾지 못했어요" 메시지
17. browser_snapshot → 전체 UI 일관성 최종 확인
18. browser_console_messages(level: "error") → 콘솔 에러 없음 확인
```

---

## Task 8: README.md 및 배포 가이드 작성

**Files:**
- Create or Modify: `README.md`

### Step 1: README.md 작성

`README.md`를 생성하거나 기존 파일을 업데이트한다. 아래 구조로 작성한다.

```markdown
# 버그버디 (BugBuddy)

사업팀/운영팀의 레드마인 이슈를 구조화하고, 개발자가 어디를 먼저 봐야 할지 빠르게 파악하도록 돕는 내부용 도구

## 주요 기능

- **이슈 템플릿 생성**: 입력 폼 → 레드마인 Description 7개 섹션 자동 구성 + 복사
- **Claude 분석**: 누락 필드 탐지, 추가 질문 생성, 추천 제목/Description
- **코드 후보 검색**: 고객사별 로컬 레포에서 키워드 기반 Top-N 파일 추천
- **Redmine 연동**: Tracker/Status 동적 로드 (미설정 시 기본값 fallback)

## 설치

### 요구사항

- Python 3.9 이상
- pip

### 의존성 설치

```bash
pip install -r requirements.txt
```

## 설정

### .env 파일 생성

`.env.example`을 복사하여 `.env`를 생성하고 값을 채운다.

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

### customers.json 작성

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

## 사용법

1. **이슈 정보 입력**: 좌측 폼에서 Tracker, Status, 고객사, 에러 내용 등 입력
2. **템플릿 생성**: "버그버디에게 정리 부탁하기" 클릭 → 우측에 7개 섹션 템플릿 생성
3. **Claude 분석** (ANTHROPIC_API_KEY 필요): "추가로 뭐가 더 필요할지 물어보기" 클릭 → 누락 필드, 추가 질문, 추천 제목 확인
4. **코드 후보 검색**: 좌측 하단에서 고객사/소스 타겟/키워드 입력 후 "추천 코드 확인하기" 클릭

## 테스트

```bash
pytest -v
```

## 주의 사항

- 환자명, 주민번호 등 PII/PHI는 입력하지 마세요. 내부 ID나 마스킹된 값을 사용하세요.
- `ANTHROPIC_API_KEY` 미설정 시 Claude 분석 기능을 사용할 수 없지만, 템플릿 생성은 정상 동작합니다.
- `REDMINE_BASE_URL` 미설정 시 Tracker/Status 기본값이 사용됩니다.
```

### Step 2: .env.example 파일 확인 및 업데이트

`.env.example`에 모든 환경변수가 포함되어 있는지 확인한다.

```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
REDMINE_BASE_URL=https://your-redmine.internal
REDMINE_API_KEY=your_redmine_api_key_here
REDMINE_PROJECT_ID=your_project_id
```

### Step 3: Commit

```bash
git add README.md .env.example
git commit -m "docs: add README with installation, config, and usage guide"
```

---

## Task 9: 전체 테스트 스위트 최종 실행 및 v1 완료 확인

**Files:**
- Modify: `tests/test_redmine_client.py` (필요 시 누락 케이스 추가)

### Step 1: 전체 pytest 실행

```bash
pytest -v --tb=short
```

Expected 출력 (누적 테스트 수):

```
tests/test_template_builder.py::...  PASSED  (Sprint 1 - 다수)
tests/test_claude_analyzer.py::...   PASSED  (Sprint 2 - 13개)
tests/test_code_searcher.py::...     PASSED  (Sprint 3 - 다수)
tests/test_redmine_client.py::...    PASSED  (Sprint 4 - 21개)

XX passed in X.XXs
```

### Step 2: Sprint 4 완료 기준 최종 체크리스트

```
Redmine 연동:
[ ] Redmine API 연동 시 Tracker/Status 목록이 API에서 동적 로드됨
[ ] @st.cache_data(ttl=300)으로 API 호출이 5분 캐싱됨

Fallback:
[ ] REDMINE_BASE_URL 미설정 시 하드코딩 값 fallback + "연동 설정이 아직 안 되어 있어요" 메시지
[ ] REDMINE_API_KEY 미설정 시 동일 fallback
[ ] API 호출 실패(401/타임아웃/연결 오류) 시 동일 fallback

메타데이터 섹션:
[ ] "Redmine 정보" expander에서 선택된 Tracker/Status 이름과 ID 표시
[ ] create_issue stub 함수 정의 (NotImplementedError 포함)

통합:
[ ] 전체 플로우 (입력 → 템플릿 → Claude 분석 → 코드 검색) 정상 동작
[ ] 모든 에러 상태 조합에서 앱 크래시 없음
[ ] 모든 버튼/메시지가 버그버디 톤 유지

문서:
[ ] pytest 전체 테스트 통과
[ ] README.md에 설치/설정/실행 가이드 포함
```

### Step 3: 최종 Commit 및 v1 태그

```bash
git add .
git commit -m "feat: complete Sprint 4 - Redmine integration and v1 release

- Implement redmine_client.py with get_trackers() and get_issue_statuses()
- Add redmine_config.py with fallback logic and UX message
- Replace hardcoded Tracker/Status dropdowns with Redmine API (surgical change)
- Cache API calls with @st.cache_data(ttl=300)
- Add Redmine metadata display section (expander)
- Add create_issue stub for v2
- Full integration and UI polish
- 21 new tests in test_redmine_client.py (all pass)
- README.md with installation, config, and usage guide"

git tag v1.0.0 -m "v1 release: Bug Buddy - Redmine issue template assistant"
```

---

## 리스크 및 대응 전략

| 리스크 | 영향도 | 완화 전략 |
|--------|--------|-----------|
| Redmine API 접근 권한 미확보 | 중간 | Should Have 기능. 실패 시 하드코딩 fallback으로 전체 기능 유지 |
| Redmine API 응답 구조가 예상과 다름 | 중간 | `.get("trackers", [])` 패턴으로 KeyError 방지, 빈 목록이면 fallback |
| `requests.get` 5초 타임아웃 초과 | 낮음 | Timeout 예외 처리로 None 반환, fallback 적용 |
| `app.py` 드롭다운 교체 시 기존 session_state 키 충돌 | 중간 | 새 키(`tracker_select`, `status_select`) 사용, 기존 키와 분리 |
| Streamlit 캐싱으로 Redmine 변경사항이 즉시 반영 안 됨 | 낮음 | TTL 5분은 내부 도구에 적합한 값. 즉시 반영 필요 시 앱 재시작 안내 |

---

## 기술 고려사항

- **Surgical Changes 원칙**: `app.py`에서 Tracker/Status 드롭다운 구성 코드 2곳만 수정. Sprint 1~3 로직은 건드리지 않는다.
- **ID 내부 매핑**: UI에는 이름만 표시 (`format_func` 사용), ID는 `session_state`에 별도 보관. 향후 `create_issue` 구현 시 활용.
- **create_issue stub**: 함수 시그니처와 docstring만 작성, 본문은 `raise NotImplementedError("v2에서 구현 예정")`. v1 범위 초과 구현 금지.
- **HTTPS 전제**: Redmine API는 HTTPS URL 사용 (`.env`의 `REDMINE_BASE_URL`이 `https://`로 시작해야 함).
- **API 키 보안**: `.env`에서만 관리, 코드 내 하드코딩 절대 금지, `.gitignore`에 `.env` 포함 확인.
